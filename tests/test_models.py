"""Test database models and constraints."""

import pytest
from sqlalchemy.exc import IntegrityError

from carms.db.models import Discipline, Program, School


def test_create_discipline(session):
    disc = Discipline(id=99, name="Test Discipline")
    session.add(disc)
    session.flush()

    result = session.get(Discipline, 99)
    assert result is not None
    assert result.name == "Test Discipline"


def test_discipline_unique_name(session):
    session.add(Discipline(id=1, name="Unique"))
    session.flush()
    session.add(Discipline(id=2, name="Unique"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_school_unique_source_id(session):
    session.add(School(source_id="123", name="School A"))
    session.flush()
    session.add(School(source_id="123", name="School B"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_program_foreign_keys(session, sample_discipline, sample_school):
    prog = Program(
        discipline_id=sample_discipline.id,
        school_id=sample_school.id,
        program_stream_id="99999",
        site="Test City",
        stream="Test Stream",
        name="Test Program",
    )
    session.add(prog)
    session.flush()
    assert prog.id is not None


def test_program_unique_stream_id(session, sample_program):
    dup = Program(
        discipline_id=sample_program.discipline_id,
        school_id=sample_program.school_id,
        program_stream_id=sample_program.program_stream_id,
        site="Other",
        stream="Other",
        name="Duplicate",
    )
    session.add(dup)
    with pytest.raises(IntegrityError):
        session.flush()
