"""Semantic search endpoint."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from carms.api.deps import get_search_service, get_session
from carms.api.schemas import SearchRequest, SearchResponse, SearchResultOut

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
def search_programs(
    request: SearchRequest,
    session: Session = Depends(get_session),
):
    """Semantic search over program descriptions."""
    service = get_search_service(session)
    results = service.search(
        query=request.query,
        top_k=request.top_k,
        discipline_id=request.discipline_id,
        school_id=request.school_id,
        site=request.site,
    )

    return SearchResponse(
        query=request.query,
        results=[
            SearchResultOut(
                program_id=r.program_id,
                program_name=r.program_name,
                discipline=r.discipline,
                school=r.school,
                site=r.site,
                stream=r.stream,
                chunk_text=r.chunk_text,
                similarity=r.similarity,
                url=r.url,
            )
            for r in results
        ],
        count=len(results),
    )
