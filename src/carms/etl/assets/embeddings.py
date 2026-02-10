"""Embedding generation asset - chunk descriptions and create vector embeddings."""

from dagster import AssetExecutionContext, AssetIn, asset
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text
from sqlmodel import SQLModel

from carms.db.models import ProgramEmbedding
from carms.etl.resources import DatabaseResource, EmbeddingResource


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

    # Create HNSW index if not exists
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
        # Clear existing embeddings
        session.execute(text("DELETE FROM program_embeddings"))
        session.commit()

        # Load all descriptions with full markdown
        rows = session.execute(
            text("""
                SELECT pd.id, pd.program_id, pd.full_markdown
                FROM program_descriptions pd
                WHERE pd.full_markdown IS NOT NULL
            """)
        ).fetchall()

        context.log.info(f"Processing {len(rows)} descriptions for embedding")

        # Batch processing
        batch_size = 64
        total_chunks = 0
        chunk_buffer: list[dict] = []

        for desc_id, program_id, markdown in rows:
            chunks = splitter.split_text(markdown)
            for i, chunk_text in enumerate(chunks):
                chunk_buffer.append(
                    {
                        "program_id": program_id,
                        "description_id": desc_id,
                        "chunk_index": i,
                        "chunk_text": chunk_text,
                    }
                )

            # Embed and insert in batches, committing each to free memory
            if len(chunk_buffer) >= batch_size:
                _embed_and_insert(session, embeddings, chunk_buffer, context)
                total_chunks += len(chunk_buffer)
                session.commit()
                chunk_buffer = []

        # Final batch
        if chunk_buffer:
            _embed_and_insert(session, embeddings, chunk_buffer, context)
            total_chunks += len(chunk_buffer)
            session.commit()

    context.log.info(f"Created {total_chunks} embedding chunks")
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

    context.log.info(f"Embedded batch of {len(chunks)} chunks")
