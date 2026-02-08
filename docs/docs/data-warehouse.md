# Data Warehouse

The CaRMS Program Explorer includes a dimensional data warehouse layer built on top of the staging tables. This provides optimized analytical queries and consolidated SQL views.

## Star Schema Design

The warehouse follows a classic **star schema** with one fact table surrounded by three dimension tables:

```mermaid
erDiagram
    DIM_DISCIPLINE {
        int discipline_key PK
        int discipline_id NK
        string discipline_name
    }
    DIM_SCHOOL {
        int school_key PK
        int school_id NK
        string school_source_id
        string school_name
    }
    DIM_SITE {
        int site_key PK
        string site_name UK
    }
    FACT_PROGRAM {
        int program_key PK
        int program_id NK
        int discipline_key FK
        int school_key FK
        int site_key FK
        string stream
        string program_name
        string url
        bool has_description
        int description_sections_filled
        int embedding_chunk_count
    }
    FACT_PROGRAM }o--|| DIM_DISCIPLINE : "discipline_key"
    FACT_PROGRAM }o--|| DIM_SCHOOL : "school_key"
    FACT_PROGRAM }o--|| DIM_SITE : "site_key"
```

## Dimension Tables

| Table | Source | Records | Description |
|-------|--------|---------|-------------|
| `dim_discipline` | `disciplines` | 37 | Medical specialties |
| `dim_school` | `schools` | ~17 | Canadian medical schools |
| `dim_site` | `programs.site` | ~50+ | Training site locations |

## Fact Table

`fact_program` contains one row per program with:

- **Foreign keys** to all three dimensions
- **Descriptive attributes**: stream, program_name, url
- **Computed measures**:
    - `has_description` — whether a program description exists
    - `description_sections_filled` — count of non-null section fields (out of 15)
    - `embedding_chunk_count` — number of vector embedding chunks

## Analytical Views

### `vw_program_summary`

Fully denormalized join of the fact table with all dimensions. Useful for ad-hoc queries without needing to remember join conditions.

### `vw_discipline_metrics`

Aggregated metrics per discipline:

- `program_count` — total programs
- `school_count` — distinct schools offering the discipline
- `site_count` — distinct training sites
- `cmg_count` / `img_count` — stream breakdown
- `avg_sections_filled` — average description completeness
- `total_chunks` — total embedding chunks

## ETL Pipeline

The warehouse assets are materialized by Dagster after the staging and embedding layers:

```
stg_disciplines → dim_discipline ─┐
stg_schools    → dim_school    ───┤
stg_programs   → dim_site      ───┤
program_embeddings ────────────────┼→ fact_program → warehouse_views
```

## API Integration

The analytics endpoints support a `use_warehouse=true` query parameter to query from warehouse views instead of raw joins:

```
GET /analytics/disciplines?use_warehouse=true
GET /analytics/schools?use_warehouse=true
```

## Design Rationale

- **Surrogate keys** (`_key` columns) decouple the warehouse from source system IDs
- **Conformed dimensions** allow consistent slicing across different analytical queries
- **Pre-computed measures** in the fact table avoid expensive runtime aggregation
- **SQL views** consolidate common join patterns, reducing query complexity
