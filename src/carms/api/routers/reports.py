"""Reports API — list and generate pandas-based reports on demand."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from carms.api.deps import get_session
from carms.reports.registry import get_report, list_reports

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/")
def reports_list():
    """List all available reports."""
    return list_reports()


@router.get("/{name}")
def reports_generate(name: str, session: Session = Depends(get_session)):
    """Generate a report by name and return as JSON."""
    report = get_report(name)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{name}' not found")
    return report.to_json(session)
