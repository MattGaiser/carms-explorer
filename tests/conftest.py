"""Test configuration and fixtures."""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlmodel import Session, SQLModel

from carms.db.models import (
    Discipline,
    Program,
    School,
)

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://carms:carms@localhost:5433/carms_test"
)


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    eng = create_engine(TEST_DATABASE_URL, echo=False)
    with eng.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    SQLModel.metadata.create_all(eng)
    yield eng
    SQLModel.metadata.drop_all(eng)


@pytest.fixture
def session(engine):
    """Yield a transactional session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    sess = Session(bind=connection)
    yield sess
    sess.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_discipline(session):
    """Create a sample discipline."""
    disc = Discipline(id=13, name="Anesthesiology")
    session.add(disc)
    session.flush()
    return disc


@pytest.fixture
def sample_school(session):
    """Create a sample school."""
    school = School(source_id="5111821", name="Memorial University of Newfoundland")
    session.add(school)
    session.flush()
    return school


@pytest.fixture
def sample_program(session, sample_discipline, sample_school):
    """Create a sample program."""
    prog = Program(
        discipline_id=sample_discipline.id,
        school_id=sample_school.id,
        program_stream_id="27447",
        site="St. John's",
        stream="CMG Stream for CMG",
        name="Memorial University / Anesthesiology / St. John's / CMG Stream",
        url="https://phx.e-carms.ca/phoenix-web/pd/ajax/program/1503/27447",
    )
    session.add(prog)
    session.flush()
    return prog


@pytest.fixture
def client(engine, session):
    """Create a FastAPI test client with DI overrides."""
    from fastapi.testclient import TestClient

    from carms.api.deps import get_session
    from carms.api.main import app

    def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
