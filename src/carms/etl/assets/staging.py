"""Staging assets - transform and upsert data into PostgreSQL."""

import pandas as pd
from dagster import AssetExecutionContext, AssetIn, asset
from sqlalchemy import text
from sqlmodel import SQLModel

from carms.db.models import Discipline, Program, ProgramDescription, School
from carms.etl.resources import DatabaseResource


@asset(
    group_name="staging",
    ins={"raw_disciplines": AssetIn()},
    compute_kind="postgres",
)
def stg_disciplines(
    context: AssetExecutionContext,
    database: DatabaseResource,
    raw_disciplines: pd.DataFrame,
) -> int:
    """Upsert disciplines into PostgreSQL."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[Discipline.__table__])

    with database.get_session() as session:
        count = 0
        for _, row in raw_disciplines.iterrows():
            disc_id = int(row["discipline_id"])
            name = str(row["discipline"])
            existing = session.get(Discipline, disc_id)
            if existing:
                existing.name = name
            else:
                session.add(Discipline(id=disc_id, name=name))
            count += 1
        session.commit()

    context.log.info(f"Upserted {count} disciplines")
    return count


@asset(
    group_name="staging",
    ins={"raw_program_master": AssetIn()},
    compute_kind="postgres",
)
def stg_schools(
    context: AssetExecutionContext,
    database: DatabaseResource,
    raw_program_master: pd.DataFrame,
) -> int:
    """Extract and upsert unique schools from program master.

    Note: source school_id is per-program, not per-school. We normalize by
    school_name and keep the first source_id seen for each school.
    """
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[School.__table__])

    # Deduplicate by school_name, keeping first source_id per school
    school_names = raw_program_master[["school_name", "school_id"]].drop_duplicates(
        subset=["school_name"]
    )

    with database.get_session() as session:
        count = 0
        for _, row in school_names.iterrows():
            source_id = str(row["school_id"])
            name = str(row["school_name"])
            existing = session.execute(School.__table__.select().where(School.name == name)).first()
            if not existing:
                session.add(School(source_id=source_id, name=name))
                count += 1
        session.commit()

    context.log.info(f"Upserted {len(school_names)} schools ({count} new)")
    return len(school_names)


@asset(
    group_name="staging",
    ins={
        "raw_program_master": AssetIn(),
        "stg_disciplines": AssetIn(),
        "stg_schools": AssetIn(),
    },
    compute_kind="postgres",
)
def stg_programs(
    context: AssetExecutionContext,
    database: DatabaseResource,
    raw_program_master: pd.DataFrame,
    stg_disciplines: int,
    stg_schools: int,
) -> int:
    """Upsert programs into PostgreSQL with FK lookups."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[Program.__table__])

    with database.get_session() as session:
        # Build school lookup: school_name -> db id
        school_rows = session.execute(text("SELECT id, name FROM schools")).fetchall()
        school_map = {row[1]: row[0] for row in school_rows}

        count = 0
        for _, row in raw_program_master.iterrows():
            psid = str(row["program_stream_id"])
            disc_id = int(row["discipline_id"])
            school_name = str(row["school_name"])
            school_id = school_map.get(school_name)
            if school_id is None:
                context.log.warning(f"School not found for name={school_name}")
                continue

            existing = session.execute(
                Program.__table__.select().where(Program.program_stream_id == psid)
            ).first()

            values = {
                "discipline_id": disc_id,
                "school_id": school_id,
                "program_stream_id": psid,
                "site": str(row["program_site"]),
                "stream": str(row["program_stream"]),
                "name": str(row["program_name"]),
                "url": str(row["program_url"]) if pd.notna(row.get("program_url")) else None,
            }

            if existing:
                session.execute(
                    Program.__table__.update()
                    .where(Program.program_stream_id == psid)
                    .values(**values)
                )
            else:
                session.add(Program(**values))
            count += 1

        session.commit()

    context.log.info(f"Upserted {count} programs")
    return count


@asset(
    group_name="staging",
    ins={
        "raw_descriptions_sectioned": AssetIn(),
        "raw_markdown_documents": AssetIn(),
        "stg_programs": AssetIn(),
    },
    compute_kind="postgres",
)
def stg_descriptions(
    context: AssetExecutionContext,
    database: DatabaseResource,
    raw_descriptions_sectioned: pd.DataFrame,
    raw_markdown_documents: list[dict],
    stg_programs: int,
) -> int:
    """Merge sectioned + markdown descriptions and upsert."""
    engine = database.get_engine()
    SQLModel.metadata.create_all(engine, tables=[ProgramDescription.__table__])

    # Build markdown lookup: program_stream_id -> page_content
    md_map = {}
    for doc in raw_markdown_documents:
        # id format: "1503|27447"
        parts = doc["id"].split("|")
        if len(parts) == 2:
            md_map[parts[1]] = doc["page_content"]

    # Section column mapping: CSV column -> model field
    section_cols = {
        "program_name": "program_name_section",
        "match_iteration_name": "match_iteration_name",
        "program_contracts": "program_contacts",
        "general_instructions": "general_instructions",
        "supporting_documentation_information": "supporting_documentation_information",
        "review_process": "review_process",
        "interviews": "interviews",
        "selection_criteria": "selection_criteria",
        "program_highlights": "program_highlights",
        "program_curriculum": "program_curriculum",
        "training_sites": "training_sites",
        "additional_information": "additional_information",
        "return_of_service": "return_of_service",
        "faq": "faq",
        "summary_of_changes": "summary_of_changes",
    }

    with database.get_session() as session:
        # Build program lookup: program_stream_id -> db id
        prog_rows = session.execute(text("SELECT id, program_stream_id FROM programs")).fetchall()
        prog_map = {row[1]: row[0] for row in prog_rows}

        count = 0
        for _, row in raw_descriptions_sectioned.iterrows():
            doc_id = str(row["document_id"])
            # Extract program_stream_id from document_id (format: "1503-27447")
            psid = doc_id.split("-")[-1] if "-" in doc_id else doc_id
            program_id = prog_map.get(psid)
            if program_id is None:
                continue

            values: dict = {"program_id": program_id, "document_id": doc_id}

            # Map section columns
            for csv_col, model_col in section_cols.items():
                val = row.get(csv_col)
                if pd.notna(val):
                    values[model_col] = str(val)

            # Add full markdown
            md_content = md_map.get(psid)
            if md_content:
                values["full_markdown"] = md_content

            existing = session.execute(
                ProgramDescription.__table__.select().where(
                    ProgramDescription.program_id == program_id
                )
            ).first()

            if existing:
                session.execute(
                    ProgramDescription.__table__.update()
                    .where(ProgramDescription.program_id == program_id)
                    .values(**values)
                )
            else:
                session.add(ProgramDescription(**values))
            count += 1

        session.commit()

    context.log.info(f"Upserted {count} descriptions")
    return count
