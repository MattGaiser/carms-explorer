"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from carms.api.deps import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(session: Session = Depends(get_session)):
    """Check API and database health."""
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}
