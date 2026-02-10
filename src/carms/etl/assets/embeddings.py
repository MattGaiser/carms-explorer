"""Embedding generation asset - chunk descriptions and create vector embeddings."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from dagster import AssetExecutionContext, AssetIn, asset
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text
from sqlmodel import Session, SQLModel

from carms.db.models import ProgramEmbedding
from carms.etl.resources import DatabaseResource, EmbeddingResource

BATCH_SIZE = 500
MAX_WORKERS = 4


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

    # Chunk all descriptions up front
    all_chunks: list[dict] = []
    for desc_id, program_id, markdown in rows:
        chunks = splitter.split_text(markdown)
        for i, chunk_text in enumerate(chunks):
            all_chunks.append(
                {
                    "program_id": program_id,
                    "description_id": desc_id,
                    "chunk_index": i,
                    "chunk_text": chunk_text,
                }
            )

    n = len(all_chunks)
    context.log.info(f"{n} chunks total, batch_size={BATCH_SIZE}, workers={MAX_WORKERS}")

    # Split into batches
    batches = [all_chunks[i : i + BATCH_SIZE] for i in range(0, len(all_chunks), BATCH_SIZE)]

    # Embed batches concurrently, insert+commit each with its own session
    total_chunks = 0

    def _process_batch(batch: list[dict]) -> int:
        """Embed a batch and insert into DB with a dedicated session."""
        texts = [c["chunk_text"] for c in batch]
        vectors = embeddings.embed(texts)

        with Session(engine) as sess:
            for chunk, vector in zip(batch, vectors):
                sess.add(
                    ProgramEmbedding(
                        program_id=chunk["program_id"],
                        description_id=chunk["description_id"],
                        chunk_index=chunk["chunk_index"],
                        chunk_text=chunk["chunk_text"],
                        embedding=vector,
                    )
                )
            sess.commit()
        return len(batch)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_batch, batch): i for i, batch in enumerate(batches)}
        for future in as_completed(futures):
            batch_idx = futures[future]
            count = future.result()
            total_chunks += count
            done = f"{total_chunks}/{n}"
            context.log.info(f"Batch {batch_idx + 1}/{len(batches)}: {count} chunks ({done})")

    context.log.info(f"Created {total_chunks} embedding chunks")
    return total_chunks
