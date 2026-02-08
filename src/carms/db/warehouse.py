"""Data warehouse star schema models for CaRMS analytics."""

from sqlmodel import Field, SQLModel


class DimDiscipline(SQLModel, table=True):
    """Discipline dimension table."""

    __tablename__ = "dim_discipline"

    discipline_key: int | None = Field(default=None, primary_key=True)
    discipline_id: int = Field(unique=True, index=True)
    discipline_name: str


class DimSchool(SQLModel, table=True):
    """School dimension table."""

    __tablename__ = "dim_school"

    school_key: int | None = Field(default=None, primary_key=True)
    school_id: int = Field(unique=True, index=True)
    school_source_id: str
    school_name: str


class DimSite(SQLModel, table=True):
    """Site dimension table."""

    __tablename__ = "dim_site"

    site_key: int | None = Field(default=None, primary_key=True)
    site_name: str = Field(unique=True)


class FactProgram(SQLModel, table=True):
    """Program fact table — central fact in the star schema."""

    __tablename__ = "fact_program"

    program_key: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(unique=True, index=True)
    discipline_key: int = Field(foreign_key="dim_discipline.discipline_key", index=True)
    school_key: int = Field(foreign_key="dim_school.school_key", index=True)
    site_key: int = Field(foreign_key="dim_site.site_key", index=True)
    stream: str
    program_name: str
    url: str | None = None
    has_description: bool = False
    description_sections_filled: int = 0
    embedding_chunk_count: int = 0
