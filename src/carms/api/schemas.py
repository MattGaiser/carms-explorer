"""Pydantic request/response models for the API."""

from pydantic import BaseModel, Field

# --- Disciplines ---


class DisciplineOut(BaseModel):
    id: int
    name: str
    program_count: int = 0


# --- Schools ---


class SchoolOut(BaseModel):
    id: int
    name: str
    program_count: int = 0


# --- Programs ---


class ProgramSummary(BaseModel):
    id: int
    name: str
    discipline: str
    school: str
    site: str
    stream: str
    url: str | None = None


class ProgramDescriptionOut(BaseModel):
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
    full_markdown: str | None = None


class ProgramDetail(ProgramSummary):
    description: ProgramDescriptionOut | None = None


# --- Search ---


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)
    discipline_id: int | None = None
    school_id: int | None = None
    site: str | None = None


class SearchResultOut(BaseModel):
    program_id: int
    program_name: str
    discipline: str
    school: str
    site: str
    stream: str
    chunk_text: str
    similarity: float
    url: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultOut]
    count: int


# --- Analytics ---


class AnalyticsOverview(BaseModel):
    total_programs: int
    total_disciplines: int
    total_schools: int
    total_embeddings: int


class DisciplineAnalytics(BaseModel):
    discipline: str
    program_count: int


class SchoolAnalytics(BaseModel):
    school: str
    program_count: int


# --- Agent ---


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str | None = None


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    has_content: bool = False
    is_relevant: bool = True
    document_type: str | None = None
    disciplines_of_interest: list[str] = []
    geographic_preferences: list[str] = []
    training_interests: list[str] = []
    research_experience: str | None = None
    clinical_experience: str | None = None
    education: str | None = None
    languages: list[str] = []
    career_goals: str | None = None
    strengths: list[str] = []
    summary: str | None = None
