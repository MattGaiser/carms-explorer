"""SQLModel database tables for CaRMS program data."""

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Index
from sqlmodel import Field, Relationship, SQLModel


class Discipline(SQLModel, table=True):
    __tablename__ = "disciplines"

    id: int = Field(primary_key=True)
    name: str = Field(index=True, unique=True)

    programs: list["Program"] = Relationship(back_populates="discipline")


class School(SQLModel, table=True):
    __tablename__ = "schools"

    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(unique=True, index=True)
    name: str = Field(index=True)

    programs: list["Program"] = Relationship(back_populates="school")


class Program(SQLModel, table=True):
    __tablename__ = "programs"

    id: int | None = Field(default=None, primary_key=True)
    discipline_id: int = Field(foreign_key="disciplines.id", index=True)
    school_id: int = Field(foreign_key="schools.id", index=True)
    program_stream_id: str = Field(unique=True, index=True)
    site: str = Field(index=True)
    stream: str
    name: str
    url: str | None = None

    discipline: Discipline | None = Relationship(back_populates="programs")
    school: School | None = Relationship(back_populates="programs")
    descriptions: list["ProgramDescription"] = Relationship(back_populates="program")
    embeddings: list["ProgramEmbedding"] = Relationship(back_populates="program")


class ProgramDescription(SQLModel, table=True):
    __tablename__ = "program_descriptions"

    id: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="programs.id", unique=True, index=True)
    document_id: str | None = None

    # Section columns matching the CSV
    program_name_section: str | None = None
    match_iteration_name: str | None = None
    program_contacts: str | None = None
    general_instructions: str | None = None
    supporting_documentation_information: str | None = None
    review_process: str | None = None
    interviews: str | None = None
    selection_criteria: str | None = None
    program_highlights: str | None = None
    program_curriculum: str | None = None
    training_sites: str | None = None
    additional_information: str | None = None
    return_of_service: str | None = None
    faq: str | None = None
    summary_of_changes: str | None = None

    # Full markdown document
    full_markdown: str | None = None

    program: Program | None = Relationship(back_populates="descriptions")
    embeddings: list["ProgramEmbedding"] = Relationship(back_populates="description")


class ProgramEmbedding(SQLModel, table=True):
    __tablename__ = "program_embeddings"

    id: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="programs.id", index=True)
    description_id: int = Field(foreign_key="program_descriptions.id", index=True)
    chunk_index: int = Field(default=0)
    chunk_text: str
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(384)),
    )

    program: Program | None = Relationship(back_populates="embeddings")
    description: ProgramDescription | None = Relationship(back_populates="embeddings")


# HNSW index for cosine similarity search
embedding_index = Index(
    "ix_program_embeddings_hnsw",
    ProgramEmbedding.embedding,  # type: ignore[arg-type]
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
