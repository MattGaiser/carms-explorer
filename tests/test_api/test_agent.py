"""Tests for agent API endpoints."""

from io import BytesIO
from unittest.mock import AsyncMock, patch

from carms.agent.pdf_profile import ApplicantProfile, store_profile


def test_agent_status_available(client):
    """Agent status endpoint returns availability."""
    with patch("carms.api.routers.agent.is_agent_available", return_value=True):
        response = client.get("/agent/status")
        assert response.status_code == 200
        assert response.json()["available"] is True


def test_agent_status_unavailable(client):
    """Agent status endpoint when agent is not available."""
    with patch("carms.api.routers.agent.is_agent_available", return_value=False):
        response = client.get("/agent/status")
        assert response.status_code == 200
        assert response.json()["available"] is False


def test_session_cleanup_clears_session_and_profile(client):
    """Session cleanup endpoint clears both session and profile."""
    with (
        patch("carms.api.routers.agent.cleanup_session") as mock_cleanup,
        patch("carms.api.routers.agent.clear_profile") as mock_clear,
    ):
        response = client.delete("/agent/session/test-session-123")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_cleanup.assert_called_once_with("test-session-123")
        mock_clear.assert_called_once_with("test-session-123")


def test_upload_rejects_non_pdf(client):
    """Upload endpoint returns 400 for non-PDF content type."""
    with patch("carms.api.routers.agent.is_agent_available", return_value=True):
        response = client.post(
            "/agent/upload",
            files={"file": ("test.txt", BytesIO(b"hello"), "text/plain")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]


def test_upload_rejects_empty_file(client):
    """Upload endpoint returns 400 for empty PDF."""
    with patch("carms.api.routers.agent.is_agent_available", return_value=True):
        response = client.post(
            "/agent/upload",
            files={"file": ("test.pdf", BytesIO(b""), "application/pdf")},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


def test_upload_rejects_invalid_pdf_magic_bytes(client):
    """Upload endpoint returns 400 when file content is not a real PDF."""
    with patch("carms.api.routers.agent.is_agent_available", return_value=True):
        response = client.post(
            "/agent/upload",
            files={"file": ("fake.pdf", BytesIO(b"NOT-A-PDF-CONTENT"), "application/pdf")},
        )
        assert response.status_code == 400
        assert "valid PDF" in response.json()["detail"]


def test_upload_requires_agent(client):
    """Upload endpoint returns 503 when agent unavailable."""
    with patch("carms.api.routers.agent.is_agent_available", return_value=False):
        response = client.post(
            "/agent/upload",
            files={"file": ("cv.pdf", BytesIO(b"%PDF-fake"), "application/pdf")},
        )
        assert response.status_code == 503


def test_upload_success(client):
    """Upload endpoint extracts profile and returns UploadResponse."""
    mock_profile = ApplicantProfile(
        session_id="sess-1",
        filename="cv.pdf",
        disciplines_of_interest=["Family Medicine", "Internal Medicine"],
        geographic_preferences=["Ontario"],
        training_interests=["rural medicine"],
        summary="A motivated applicant interested in family medicine.",
    )

    with (
        patch("carms.api.routers.agent.is_agent_available", return_value=True),
        patch(
            "carms.api.routers.agent.extract_profile_from_pdf",
            new_callable=AsyncMock,
            return_value=mock_profile,
        ),
    ):
        response = client.post(
            "/agent/upload",
            files={"file": ("cv.pdf", BytesIO(b"%PDF-fake"), "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-1"
        assert data["filename"] == "cv.pdf"
        assert data["has_content"] is True
        assert "Family Medicine" in data["disciplines_of_interest"]
        assert data["geographic_preferences"] == ["Ontario"]
        assert data["summary"] is not None


def test_upload_returns_502_on_extraction_failure(client):
    """Upload endpoint returns 502 when Anthropic API fails."""
    with (
        patch("carms.api.routers.agent.is_agent_available", return_value=True),
        patch(
            "carms.api.routers.agent.extract_profile_from_pdf",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Profile extraction failed: rate limit"),
        ),
    ):
        response = client.post(
            "/agent/upload",
            files={"file": ("cv.pdf", BytesIO(b"%PDF-fake"), "application/pdf")},
        )
        assert response.status_code == 502
        assert "extraction failed" in response.json()["detail"].lower()


def test_chat_prepends_profile_context(client):
    """Chat endpoint prepends profile context when a profile exists for the session."""
    profile = ApplicantProfile(
        session_id="sess-with-profile",
        filename="cv.pdf",
        disciplines_of_interest=["Pediatrics"],
        geographic_preferences=["BC"],
    )
    store_profile(profile)

    captured_message = None

    async def mock_query(msg):
        nonlocal captured_message
        captured_message = msg

    with (
        patch("carms.api.routers.agent.is_agent_available", return_value=True),
        patch("carms.api.routers.agent.create_client", new_callable=AsyncMock) as mock_create,
    ):
        mock_client = AsyncMock()
        mock_client.query = mock_query

        # Make receive_response return an empty async iterator
        async def empty_iter():
            return
            yield  # noqa: unreachable — makes this an async generator

        mock_client.receive_response = empty_iter
        mock_create.return_value = mock_client

        response = client.post(
            "/agent/chat",
            json={"message": "Find matching programs", "session_id": "sess-with-profile"},
        )
        assert response.status_code == 200
        assert captured_message is not None
        assert "[APPLICANT PROFILE" in captured_message
        assert "Pediatrics" in captured_message
        assert "Find matching programs" in captured_message

    # Clean up
    from carms.agent.pdf_profile import clear_profile
    clear_profile("sess-with-profile")


def test_chat_message_max_length(client):
    """Chat endpoint rejects messages exceeding max_length."""
    with patch("carms.api.routers.agent.is_agent_available", return_value=True):
        response = client.post(
            "/agent/chat",
            json={"message": "x" * 10001, "session_id": "test"},
        )
        assert response.status_code == 422
