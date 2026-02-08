"""Tests for SearchService retriever."""

import pytest

from carms.db.models import ProgramDescription, ProgramEmbedding
from carms.search.retriever import SearchService


@pytest.fixture
def sample_embedding(session, sample_program):
    """Create a sample program with description and embedding."""
    desc = ProgramDescription(
        program_id=sample_program.id,
        program_highlights="Excellent rural training opportunities",
        full_markdown="# Test Program\n\nExcellent rural training.",
    )
    session.add(desc)
    session.flush()

    # 384-dim zero vector (valid for pgvector)
    zero_vector = [0.0] * 384
    emb = ProgramEmbedding(
        program_id=sample_program.id,
        description_id=desc.id,
        chunk_index=0,
        chunk_text="Excellent rural training opportunities in family medicine.",
        embedding=zero_vector,
    )
    session.add(emb)
    session.flush()
    return emb


class TestSearchService:
    def test_search_returns_list(self, session, sample_embedding):
        service = SearchService(session)
        results = service.search("rural medicine", top_k=5)
        assert isinstance(results, list)

    def test_search_result_structure(self, session, sample_embedding):
        service = SearchService(session)
        results = service.search("rural medicine", top_k=5)
        if results:
            r = results[0]
            assert hasattr(r, "program_id")
            assert hasattr(r, "program_name")
            assert hasattr(r, "discipline")
            assert hasattr(r, "school")
            assert hasattr(r, "site")
            assert hasattr(r, "stream")
            assert hasattr(r, "chunk_text")
            assert hasattr(r, "similarity")

    def test_filter_by_discipline(self, session, sample_embedding):
        service = SearchService(session)
        # Use a discipline_id that doesn't exist
        results = service.search("rural", top_k=5, discipline_id=9999)
        assert results == []

    def test_nonexistent_filter_returns_empty(self, session, sample_embedding):
        service = SearchService(session)
        results = service.search("rural", top_k=5, site="Nonexistent City XYZ")
        assert results == []
