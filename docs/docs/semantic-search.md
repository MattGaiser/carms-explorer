# Semantic Search

## How It Works

1. **Document Chunking**: Program descriptions (full markdown) are split into overlapping chunks using LangChain's `RecursiveCharacterTextSplitter` (512 chars, 64 overlap)
2. **Embedding**: Each chunk is embedded using `all-MiniLM-L6-v2` (384-dimensional vectors, ~80MB model)
3. **Storage**: Embeddings are stored in PostgreSQL via the `pgvector` extension with an HNSW index
4. **Query**: User queries are embedded with the same model, then matched against stored chunks using cosine similarity

## Why This Approach

- **No API key required**: The embedding model runs locally, making the search feature work out of the box
- **Chunk-level retrieval**: Rather than 1 vector per document, chunking captures different aspects of each program description
- **pgvector HNSW index**: Fast approximate nearest neighbor search, scales well to thousands of chunks
- **Filter support**: SQL WHERE clauses combine with vector search for hybrid filtering

## Model Details

| Property | Value |
|----------|-------|
| Model | `all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Max tokens | 256 |
| Size | ~80MB |
| Speed | ~100 embeddings/second |
| Normalization | L2-normalized (cosine = dot product) |

## HNSW Index Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `m` | 16 | Max connections per node |
| `ef_construction` | 64 | Build-time search width |
| Distance | cosine | `vector_cosine_ops` |
