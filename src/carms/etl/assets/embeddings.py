"""Embedding generation asset - chunk descriptions and create vector embeddings."""

from dagster import AssetExecutionContext, AssetIn, asset
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text
from sqlmodel import SQLModel

from carms.db.models import ProgramEmbedding
from carms.etl.resources import DatabaseResource, EmbeddingResource

EMBED_BATCH_SIZE = 500


@asset(
    group_name="embeddings",
    ins={"stg_descriptions": AssetIn()},
    compute_kind="ml",
)
def program_embeddings(
    context: AssetExecutionContext,
    database: DatabaseResource,
    embeddings: EmbeddingResource,
    stg_descriptions: int,
) -> int:
    """Chunk program descriptions and generate embeddings."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[ProgramEmbedding.__table__])

    with engine.connect() as conn:
        conn.execute(
            text("""
                CREATE INDEX IF NOT EXISTS ix_program_embeddings_hnsw
                ON program_embeddings
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64)
            """)
        )
        conn.commit()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n# ", "\n## ", "\n### ", "\n", " "],
    )

    with database.get_session() as session:
        session.execute(text("DELETE FROM program_embeddings"))
        session.commit()

        # Stream rows one at a time to avoid loading all markdown into memory
        result = session.execute(
            text("""
                SELECT pd.id, pd.program_id, pd.full_markdown
                FROM program_descriptions pd
                WHERE pd.full_markdown IS NOT NULL
            """)
        )

        total_chunks = 0
        chunk_buffer: list[dict] = []
        program_count = 0

        for desc_id, program_id, markdown in result:
            program_count += 1
            chunks = splitter.split_text(markdown)
            for i, chunk_text in enumerate(chunks):
                chunk_buffer.append({
                    "program_id": program_id,
                    "description_id": desc_id,
                    "chunk_index": i,
                    "chunk_text": chunk_text,
                })

            # Embed and commit when buffer is large enough
            if len(chunk_buffer) >= EMBED_BATCH_SIZE:
                _embed_and_insert(
                    session, embeddings, chunk_buffer, context,
                )
                total_chunks += len(chunk_buffer)
                session.commit()
                context.log.info(
                    f"Programs: {program_count}, chunks: {total_chunks}"
                )
                chunk_buffer = []

        # Final batch
        if chunk_buffer:
            _embed_and_insert(session, embeddings, chunk_buffer, context)
            total_chunks += len(chunk_buffer)
            session.commit()

    context.log.info(f"Done: {total_chunks} chunks from {program_count} programs")
    return total_chunks


def _embed_and_insert(
    session,
    embedding_resource: EmbeddingResource,
    chunks: list[dict],
    context: AssetExecutionContext,
) -> None:
    """Embed a batch of chunks and insert into database."""
    texts = [c["chunk_text"] for c in chunks]
    vectors = embedding_resource.embed(texts)

    for chunk, vector in zip(chunks, vectors):
        session.add(
            ProgramEmbedding(
                program_id=chunk["program_id"],
                description_id=chunk["description_id"],
                chunk_index=chunk["chunk_index"],
                chunk_text=chunk["chunk_text"],
                embedding=vector,
            )
        )
