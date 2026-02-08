"""FastAPI dependency injection."""

from collections.abc import Generator

from sqlmodel import Session

from carms.db.engine import engine
from carms.search.retriever import SearchService


def get_session() -> Generator[Session]:
    """Yield a database session per request."""
    with Session(engine) as session:
        yield session


def get_search_service(session: Session) -> SearchService:
    """Create a search service with the current session."""
    return SearchService(session)
