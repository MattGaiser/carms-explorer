"""Analytics endpoints for aggregate program data."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlmodel import Session, select

from carms.api.deps import get_session
from carms.api.schemas import (
    AnalyticsOverview,
    DisciplineAnalytics,
    SchoolAnalytics,
)
from carms.db.models import Discipline, Program, School

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def analytics_overview(session: Session = Depends(get_session)):
    """Get aggregate counts."""
    programs = session.execute(select(func.count(Program.id))).scalar_one()
    disciplines = session.execute(select(func.count(Discipline.id))).scalar_one()
    schools = session.execute(select(func.count(School.id))).scalar_one()
    embeddings = session.execute(text("SELECT COUNT(*) FROM program_embeddings")).scalar_one()

    return AnalyticsOverview(
        total_programs=programs,
        total_disciplines=disciplines,
        total_schools=schools,
        total_embeddings=embeddings,
    )


@router.get("/disciplines", response_model=list[DisciplineAnalytics])
def analytics_disciplines(
    session: Session = Depends(get_session),
    use_warehouse: bool = Query(
        False, description="Query from warehouse views instead of raw tables"
    ),
):
    """Program count by discipline, sorted descending."""
    if use_warehouse:
        rows = session.execute(
            text(
                "SELECT discipline, program_count "
                "FROM vw_discipline_metrics ORDER BY program_count DESC"
            )
        ).all()
        return [DisciplineAnalytics(discipline=row[0], program_count=row[1]) for row in rows]

    rows = session.execute(
        select(Discipline.name, func.count(Program.id).label("cnt"))
        .join(Program, Discipline.id == Program.discipline_id)
        .group_by(Discipline.name)
        .order_by(func.count(Program.id).desc())
    ).all()

    return [DisciplineAnalytics(discipline=row[0], program_count=row[1]) for row in rows]


@router.get("/schools", response_model=list[SchoolAnalytics])
def analytics_schools(
    session: Session = Depends(get_session),
    use_warehouse: bool = Query(
        False, description="Query from warehouse views instead of raw tables"
    ),
):
    """Program count by school, sorted descending."""
    if use_warehouse:
        rows = session.execute(
            text("""
                SELECT school_name, COUNT(*) AS program_count
                FROM vw_program_summary
                GROUP BY school_name
                ORDER BY program_count DESC
            """)
        ).all()
        return [SchoolAnalytics(school=row[0], program_count=row[1]) for row in rows]

    rows = session.execute(
        select(School.name, func.count(Program.id).label("cnt"))
        .join(Program, School.id == Program.school_id)
        .group_by(School.name)
        .order_by(func.count(Program.id).desc())
    ).all()

    return [SchoolAnalytics(school=row[0], program_count=row[1]) for row in rows]
