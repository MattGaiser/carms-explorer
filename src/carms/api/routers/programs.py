"""Program endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from carms.api.deps import get_session
from carms.api.schemas import ProgramDescriptionOut, ProgramDetail, ProgramSummary
from carms.db.models import Discipline, Program, ProgramDescription, School

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("/", response_model=list[ProgramSummary])
def list_programs(
    discipline_id: int | None = Query(None),
    school_id: int | None = Query(None),
    site: str | None = Query(None),
    q: str | None = Query(None, description="Text search in program name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """List programs with optional filters."""
    stmt = (
        select(Program, Discipline.name.label("discipline_name"), School.name.label("school_name"))
        .join(Discipline, Program.discipline_id == Discipline.id)
        .join(School, Program.school_id == School.id)
    )

    if discipline_id is not None:
        stmt = stmt.where(Program.discipline_id == discipline_id)
    if school_id is not None:
        stmt = stmt.where(Program.school_id == school_id)
    if site is not None:
        stmt = stmt.where(Program.site.ilike(f"%{site}%"))  # type: ignore[union-attr]
    if q is not None:
        stmt = stmt.where(Program.name.ilike(f"%{q}%"))  # type: ignore[union-attr]

    stmt = stmt.order_by(Program.name).offset(offset).limit(limit)
    rows = session.execute(stmt).all()

    return [
        ProgramSummary(
            id=prog.id,  # type: ignore[arg-type]
            name=prog.name,
            discipline=disc_name,
            school=school_name,
            site=prog.site,
            stream=prog.stream,
            url=prog.url,
        )
        for prog, disc_name, school_name in rows
    ]


@router.get("/{program_id}", response_model=ProgramDetail)
def get_program(program_id: int, session: Session = Depends(get_session)):
    """Get program detail with full description."""
    row = session.execute(
        select(Program, Discipline.name.label("discipline_name"), School.name.label("school_name"))
        .join(Discipline, Program.discipline_id == Discipline.id)
        .join(School, Program.school_id == School.id)
        .where(Program.id == program_id)
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Program not found")

    prog, disc_name, school_name = row

    # Get description
    desc = session.execute(
        select(ProgramDescription).where(ProgramDescription.program_id == program_id)
    ).scalar_one_or_none()

    desc_out = None
    if desc:
        desc_out = ProgramDescriptionOut(
            program_name_section=desc.program_name_section,
            match_iteration_name=desc.match_iteration_name,
            program_contacts=desc.program_contacts,
            general_instructions=desc.general_instructions,
            supporting_documentation_information=desc.supporting_documentation_information,
            review_process=desc.review_process,
            interviews=desc.interviews,
            selection_criteria=desc.selection_criteria,
            program_highlights=desc.program_highlights,
            program_curriculum=desc.program_curriculum,
            training_sites=desc.training_sites,
            additional_information=desc.additional_information,
            return_of_service=desc.return_of_service,
            faq=desc.faq,
            summary_of_changes=desc.summary_of_changes,
            full_markdown=desc.full_markdown,
        )

    return ProgramDetail(
        id=prog.id,  # type: ignore[arg-type]
        name=prog.name,
        discipline=disc_name,
        school=school_name,
        site=prog.site,
        stream=prog.stream,
        url=prog.url,
        description=desc_out,
    )
