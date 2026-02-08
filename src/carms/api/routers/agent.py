"""Agent chat endpoint with SSE streaming and PDF upload."""

import json
import logging
import uuid

from fastapi import APIRouter, HTTPException, UploadFile
from sse_starlette.sse import EventSourceResponse

from carms.agent.agent import (
    cleanup_session,
    create_client,
    is_agent_available,
    store_claude_session,
)
from carms.agent.pdf_profile import (
    MAX_UPLOAD_SIZE,
    clear_profile,
    extract_profile_from_pdf,
    format_profile_context,
    get_profile,
    is_valid_pdf,
)
from carms.api.schemas import ChatRequest, UploadResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/status")
async def agent_status():
    """Check if the AI agent is available."""
    return {"available": is_agent_available()}


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile, session_id: str | None = None):
    """Upload a PDF document for applicant profile extraction."""
    if not is_agent_available():
        raise HTTPException(
            status_code=503,
            detail="AI agent not available. Set ANTHROPIC_API_KEY to enable.",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(pdf_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
        )

    if not is_valid_pdf(pdf_bytes):
        raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF.")

    sid = session_id or str(uuid.uuid4())

    try:
        profile = await extract_profile_from_pdf(pdf_bytes, file.filename or "upload.pdf", sid)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return UploadResponse(
        session_id=profile.session_id,
        filename=profile.filename,
        has_content=profile.has_content,
        is_relevant=profile.is_relevant,
        document_type=profile.document_type,
        disciplines_of_interest=profile.disciplines_of_interest,
        geographic_preferences=profile.geographic_preferences,
        training_interests=profile.training_interests,
        research_experience=profile.research_experience,
        clinical_experience=profile.clinical_experience,
        education=profile.education,
        languages=profile.languages,
        career_goals=profile.career_goals,
        strengths=profile.strengths,
        summary=profile.summary,
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat with the CaRMS AI agent via SSE streaming.

    Each request creates a fresh ClaudeSDKClient. Multi-turn context is
    maintained by resuming the Claude Code session via the ``resume`` option.

    If an applicant profile has been uploaded for this session, it is
    prepended to the user message so the agent can use it for matching.
    """
    if not is_agent_available():
        raise HTTPException(
            status_code=503,
            detail="AI agent not available. Set ANTHROPIC_API_KEY to enable.",
        )

    session_id = request.session_id or str(uuid.uuid4())

    # Prepend applicant profile context if one exists and has content
    message = request.message
    profile = get_profile(session_id)
    if profile and profile.has_content:
        message = format_profile_context(profile) + "\n\n" + message

    async def event_generator():
        from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock

        client = await create_client(session_id)
        try:
            await client.query(message)

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, ToolUseBlock):
                            yield {
                                "event": "tool_use",
                                "data": json.dumps(
                                    {
                                        "tool": block.name,
                                        "input": block.input,
                                    }
                                ),
                            }
                        elif isinstance(block, TextBlock):
                            yield {
                                "event": "text",
                                "data": json.dumps({"text": block.text}),
                            }
                elif isinstance(msg, ResultMessage):
                    store_claude_session(session_id, msg.session_id)
                    yield {
                        "event": "result",
                        "data": json.dumps(
                            {
                                "session_id": session_id,
                                "is_error": msg.is_error,
                            }
                        ),
                    }

        except Exception as e:
            logging.getLogger(__name__).error("Agent error for session %s: %s", session_id, e)
            yield {
                "event": "error",
                "data": json.dumps({"error": "An error occurred processing your request."}),
            }
            cleanup_session(session_id)
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    return EventSourceResponse(event_generator())


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clean up a chat session and any associated profile."""
    cleanup_session(session_id)
    clear_profile(session_id)
    return {"status": "ok"}
