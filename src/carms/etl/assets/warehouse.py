"""Dagster assets for the data warehouse star schema."""

from dagster import AssetExecutionContext, AssetIn, asset
from sqlalchemy import text
from sqlmodel import SQLModel

from carms.db.warehouse import DimDiscipline, DimSchool, DimSite, FactProgram
from carms.etl.resources import DatabaseResource


@asset(
    group_name="warehouse",
    ins={"stg_disciplines": AssetIn()},
    compute_kind="postgres",
)
def dim_discipline(
    context: AssetExecutionContext,
    database: DatabaseResource,
    stg_disciplines: int,
) -> int:
    """Load discipline dimension from staging."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[DimDiscipline.__table__])

    with database.get_session() as session:
        session.execute(text("TRUNCATE dim_discipline CASCADE"))
        rows = session.execute(text("SELECT id, name FROM disciplines")).fetchall()
        for disc_id, name in rows:
            session.add(DimDiscipline(discipline_id=disc_id, discipline_name=name))
        session.commit()

    context.log.info(f"Loaded {len(rows)} discipline dimensions")
    return len(rows)


@asset(
    group_name="warehouse",
    ins={"stg_schools": AssetIn()},
    compute_kind="postgres",
)
def dim_school(
    context: AssetExecutionContext,
    database: DatabaseResource,
    stg_schools: int,
) -> int:
    """Load school dimension from staging."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[DimSchool.__table__])

    with database.get_session() as session:
        session.execute(text("TRUNCATE dim_school CASCADE"))
        rows = session.execute(text("SELECT id, source_id, name FROM schools")).fetchall()
        for school_id, source_id, name in rows:
            session.add(
                DimSchool(school_id=school_id, school_source_id=source_id, school_name=name)
            )
        session.commit()

    context.log.info(f"Loaded {len(rows)} school dimensions")
    return len(rows)


@asset(
    group_name="warehouse",
    ins={"stg_programs": AssetIn()},
    compute_kind="postgres",
)
def dim_site(
    context: AssetExecutionContext,
    database: DatabaseResource,
    stg_programs: int,
) -> int:
    """Load site dimension from unique program sites."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[DimSite.__table__])

    with database.get_session() as session:
        session.execute(text("TRUNCATE dim_site CASCADE"))
        rows = session.execute(text("SELECT DISTINCT site FROM programs ORDER BY site")).fetchall()
        for (site_name,) in rows:
            session.add(DimSite(site_name=site_name))
        session.commit()

    context.log.info(f"Loaded {len(rows)} site dimensions")
    return len(rows)


@asset(
    group_name="warehouse",
    ins={
        "dim_discipline": AssetIn(),
        "dim_school": AssetIn(),
        "dim_site": AssetIn(),
        "program_embeddings": AssetIn(),
    },
    compute_kind="postgres",
)
def fact_program(
    context: AssetExecutionContext,
    database: DatabaseResource,
    dim_discipline: int,
    dim_school: int,
    dim_site: int,
    program_embeddings: int,
) -> int:
    """Load fact table joining programs with all dimensions and computed measures."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[FactProgram.__table__])

    section_cols = [
        "program_name_section",
        "match_iteration_name",
        "program_contacts",
        "general_instructions",
        "supporting_documentation_information",
        "review_process",
        "interviews",
        "selection_criteria",
        "program_highlights",
        "program_curriculum",
        "training_sites",
        "additional_information",
        "return_of_service",
        "faq",
        "summary_of_changes",
    ]
    sections_case = " + ".join(
        f"CASE WHEN pd.{col} IS NOT NULL THEN 1 ELSE 0 END" for col in section_cols
    )

    with database.get_session() as session:
        session.execute(text("TRUNCATE fact_program"))
        session.execute(
            text(f"""
                INSERT INTO fact_program (
                    program_id, discipline_key, school_key, site_key,
                    stream, program_name, url,
                    has_description, description_sections_filled, embedding_chunk_count
                )
                SELECT
                    p.id,
                    dd.discipline_key,
                    ds.school_key,
                    dst.site_key,
                    p.stream,
                    p.name,
                    p.url,
                    CASE WHEN pd.id IS NOT NULL THEN true ELSE false END,
                    COALESCE({sections_case}, 0),
                    COALESCE(ec.chunk_count, 0)
                FROM programs p
                JOIN dim_discipline dd ON p.discipline_id = dd.discipline_id
                JOIN dim_school ds ON p.school_id = ds.school_id
                JOIN dim_site dst ON p.site = dst.site_name
                LEFT JOIN program_descriptions pd ON p.id = pd.program_id
                LEFT JOIN (
                    SELECT program_id, COUNT(*) AS chunk_count
                    FROM program_embeddings
                    GROUP BY program_id
                ) ec ON p.id = ec.program_id
            """)
        )
        count = session.execute(text("SELECT COUNT(*) FROM fact_program")).scalar_one()
        session.commit()

    context.log.info(f"Loaded {count} fact rows")
    return count


@asset(
    group_name="warehouse",
    ins={"fact_program": AssetIn()},
    compute_kind="postgres",
)
def warehouse_views(
    context: AssetExecutionContext,
    database: DatabaseResource,
    fact_program: int,
) -> int:
    """Create analytical SQL views on the star schema."""
    from carms.db.views import create_views

    with database.get_session() as session:
        create_views(session)

    context.log.info("Created warehouse views: vw_program_summary, vw_discipline_metrics")
    return 2
