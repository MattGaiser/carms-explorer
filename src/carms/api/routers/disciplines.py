"""Discipline endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from carms.api.deps import get_session
from carms.api.schemas import DisciplineOut
from carms.db.models import Discipline, Program

router = APIRouter(prefix="/disciplines", tags=["disciplines"])


@router.get("/", response_model=list[DisciplineOut])
def list_disciplines(session: Session = Depends(get_session)):
    """List all disciplines with program counts."""
    rows = session.execute(
        select(
            Discipline.id,
            Discipline.name,
            func.count(Program.id).label("program_count"),
        )
        .outerjoin(Program, Discipline.id == Program.discipline_id)
        .group_by(Discipline.id, Discipline.name)
        .order_by(Discipline.name)
    ).all()

    return [DisciplineOut(id=row[0], name=row[1], program_count=row[2]) for row in rows]
