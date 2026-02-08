"""SQL views for the data warehouse layer."""

from sqlalchemy import text
from sqlmodel import Session


def create_views(session: Session) -> None:
    """Create or replace warehouse analytical views."""

    # Denormalized program summary view
    session.execute(
        text("""
            CREATE OR REPLACE VIEW vw_program_summary AS
            SELECT
                f.program_key,
                f.program_id,
                f.program_name,
                f.stream,
                f.url,
                f.has_description,
                f.description_sections_filled,
                f.embedding_chunk_count,
                dd.discipline_id,
                dd.discipline_name,
                ds.school_id,
                ds.school_source_id,
                ds.school_name,
                dst.site_name
            FROM fact_program f
            JOIN dim_discipline dd ON f.discipline_key = dd.discipline_key
            JOIN dim_school ds ON f.school_key = ds.school_key
            JOIN dim_site dst ON f.site_key = dst.site_key
        """)
    )

    # Aggregated discipline metrics view
    session.execute(
        text("""
            CREATE OR REPLACE VIEW vw_discipline_metrics AS
            SELECT
                dd.discipline_name AS discipline,
                COUNT(f.program_key) AS program_count,
                COUNT(DISTINCT ds.school_key) AS school_count,
                COUNT(DISTINCT dst.site_key) AS site_count,
                SUM(CASE WHEN f.stream ILIKE '%%CMG%%' THEN 1 ELSE 0 END) AS cmg_count,
                SUM(CASE WHEN f.stream ILIKE '%%IMG%%' THEN 1 ELSE 0 END) AS img_count,
                ROUND(AVG(f.description_sections_filled), 1) AS avg_sections_filled,
                SUM(f.embedding_chunk_count) AS total_chunks
            FROM fact_program f
            JOIN dim_discipline dd ON f.discipline_key = dd.discipline_key
            JOIN dim_school ds ON f.school_key = ds.school_key
            JOIN dim_site dst ON f.site_key = dst.site_key
            GROUP BY dd.discipline_name
            ORDER BY program_count DESC
        """)
    )

    session.commit()
