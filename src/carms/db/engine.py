"""SQLAlchemy engine and session factory."""

from sqlalchemy import create_engine
from sqlmodel import Session

from carms.config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def get_session():
    """Yield a database session."""
    with Session(engine) as session:
        yield session
