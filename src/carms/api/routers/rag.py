"""RAG endpoint — LangChain-powered question answering over program data."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=8, ge=1, le=30)


class RAGSource(BaseModel):
    program_name: str | None = None
    discipline: str | None = None
    school: str | None = None
    site: str | None = None
    similarity: float | None = None
    excerpt: str | None = None


class RAGResponse(BaseModel):
    question: str
    answer: str
    sources: list[RAGSource]


@router.post("/ask", response_model=RAGResponse)
def rag_ask(request: RAGRequest):
    """Answer a question using LangChain RAG over CaRMS program descriptions."""
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="RAG not available. Set ANTHROPIC_API_KEY to enable.",
        )

    from carms.search.rag import ask

    result = ask(question=request.question, k=request.top_k)
    return RAGResponse(
        question=request.question,
        answer=result["answer"],
        sources=[RAGSource(**s) for s in result["sources"]],
    )
