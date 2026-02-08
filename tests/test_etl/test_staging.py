"""Tests for staging layer — upsert behavior and constraints."""

from carms.db.models import Discipline, Program, ProgramDescription, School


class TestStgDisciplines:
    def test_create_discipline(self, session):
        disc = Discipline(id=1, name="Family Medicine")
        session.add(disc)
        session.flush()
        assert disc.id == 1
        assert disc.name == "Family Medicine"

    def test_update_discipline(self, session):
        disc = Discipline(id=2, name="Pediatrics")
        session.add(disc)
        session.flush()
        disc.name = "Paediatrics"
        session.flush()
        loaded = session.get(Discipline, 2)
        assert loaded.name == "Paediatrics"


class TestStgSchools:
    def test_create_school(self, session):
        school = School(source_id="999", name="Test University")
        session.add(school)
        session.flush()
        assert school.id is not None
        assert school.name == "Test University"

    def test_unique_source_id(self, session):
        import pytest
        from sqlalchemy.exc import IntegrityError

        session.add(School(source_id="111", name="School A"))
        session.flush()
        session.add(School(source_id="111", name="School B"))
        with pytest.raises(IntegrityError):
            session.flush()


class TestStgPrograms:
    def test_fk_creation(self, session, sample_discipline, sample_school):
        prog = Program(
            discipline_id=sample_discipline.id,
            school_id=sample_school.id,
            program_stream_id="99999",
            site="Test City",
            stream="CMG",
            name="Test Program",
        )
        session.add(prog)
        session.flush()
        assert prog.id is not None
        assert prog.discipline_id == sample_discipline.id
        assert prog.school_id == sample_school.id

    def test_update_preserves_id(self, session, sample_program):
        original_id = sample_program.id
        sample_program.name = "Updated Name"
        session.flush()
        assert sample_program.id == original_id
        assert sample_program.name == "Updated Name"


class TestStgDescriptions:
    def test_linked_to_program(self, session, sample_program):
        desc = ProgramDescription(
            program_id=sample_program.id,
            program_highlights="Great program",
        )
        session.add(desc)
        session.flush()
        assert desc.id is not None
        assert desc.program_id == sample_program.id

    def test_unique_per_program(self, session, sample_program):
        import pytest
        from sqlalchemy.exc import IntegrityError

        session.add(ProgramDescription(program_id=sample_program.id))
        session.flush()
        session.add(ProgramDescription(program_id=sample_program.id))
        with pytest.raises(IntegrityError):
            session.flush()
