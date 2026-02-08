"""PDF upload → applicant profile extraction using Anthropic API."""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field

import anthropic

from carms.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "claude-sonnet-4-5-20250929"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
PDF_MAGIC = b"%PDF-"

EXTRACTION_PROMPT = """\
You are an expert career counselor. A user uploaded a document to a medical residency program \
matching tool (CaRMS). Your FIRST task is to determine if this document is relevant.

A document is RELEVANT only if it is one of these:
- CV / resume (of a medical student or professional)
- Personal statement or cover letter (for residency applications)
- CaRMS application or supplementary document
- Academic transcript
- Letter of recommendation for a medical applicant
- Research portfolio or publication list

A document is NOT RELEVANT if it is anything else, including but not limited to:
- Airline bookings, travel confirmations, receipts, invoices
- Government forms, rebate applications, tax documents
- News articles, marketing materials, manuals
- Non-medical resumes or job applications

Set "is_relevant" to false if the document does not clearly relate to a medical career or \
residency application. When in doubt, mark it as NOT relevant.

Return **only** valid JSON (no markdown fences, no explanation) with these keys:

{
  "is_relevant": true or false,
  "document_type": "what kind of document this is, e.g. 'CV', 'personal statement'",
  "disciplines_of_interest": ["medical specialties, rotations, or fields mentioned"],
  "geographic_preferences": ["provinces, cities, regions, or institutions mentioned"],
  "training_interests": ["specific training focuses mentioned, e.g. rural medicine, research"],
  "research_experience": "brief summary of any research mentioned, or null",
  "clinical_experience": "brief summary of clinical experience or rotations, or null",
  "education": "degrees, institutions, and years if mentioned, or null",
  "languages": ["languages mentioned or implied"],
  "career_goals": "any stated career goals or aspirations, or null",
  "strengths": ["key strengths, skills, awards, or qualities mentioned"],
  "summary": "2-3 sentence overall summary of the applicant based on the document"
}

If "is_relevant" is false, leave all profile fields as null/[] and just fill in "document_type" \
and set "summary" to a brief description of what the document actually is.

If "is_relevant" is true, be thorough extracting information:
- If the document mentions a university, include it under "education"
- If it mentions a city or province, consider it a geographic preference
- If it lists clinical rotations or electives, those indicate disciplines of interest
- If it mentions research projects, summarize them under "research_experience"
- Any medical specialty mentioned anywhere is a discipline of interest
- Prefer extracting something over returning empty — partial info helps
"""


@dataclass
class ApplicantProfile:
    session_id: str
    filename: str
    is_relevant: bool = True
    document_type: str | None = None
    disciplines_of_interest: list[str] = field(default_factory=list)
    geographic_preferences: list[str] = field(default_factory=list)
    training_interests: list[str] = field(default_factory=list)
    research_experience: str | None = None
    clinical_experience: str | None = None
    education: str | None = None
    languages: list[str] = field(default_factory=list)
    career_goals: str | None = None
    strengths: list[str] = field(default_factory=list)
    summary: str | None = None

    @property
    def has_content(self) -> bool:
        """True if the document is relevant and at least one meaningful field was extracted."""
        if not self.is_relevant:
            return False
        return bool(
            self.disciplines_of_interest
            or self.geographic_preferences
            or self.training_interests
            or self.research_experience
            or self.clinical_experience
            or self.education
            or self.languages
            or self.career_goals
            or self.strengths
            or self.summary
        )


# In-memory storage keyed by session_id (same pattern as _claude_sessions in agent.py)
_session_profiles: dict[str, ApplicantProfile] = {}


def store_profile(profile: ApplicantProfile) -> None:
    _session_profiles[profile.session_id] = profile


def get_profile(session_id: str) -> ApplicantProfile | None:
    return _session_profiles.get(session_id)


def clear_profile(session_id: str) -> None:
    _session_profiles.pop(session_id, None)


def is_valid_pdf(data: bytes) -> bool:
    """Check PDF magic bytes."""
    return data[:5] == PDF_MAGIC


def _ensure_str_list(value: object) -> list[str]:
    """Coerce LLM output to list[str], handling string-instead-of-list cases."""
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def _ensure_optional_str(value: object) -> str | None:
    """Coerce LLM output to Optional[str]."""
    if value is None:
        return None
    if isinstance(value, str):
        return value or None
    return str(value)


async def extract_profile_from_pdf(
    pdf_bytes: bytes,
    filename: str,
    session_id: str,
) -> ApplicantProfile:
    """Send PDF to Anthropic API for structured profile extraction."""
    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("ascii")

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await client.messages.create(
            model=EXTRACTION_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )
    except anthropic.APIError as e:
        logger.error("Anthropic API error during profile extraction: %s", e)
        raise RuntimeError(f"Profile extraction failed: {e.message}") from e

    if not response.content:
        logger.warning("Anthropic API returned empty content for profile extraction")
        data = {}
    else:
        raw_text = response.content[0].text
        logger.debug("Profile extraction raw response: %s", raw_text)

        # Strip markdown fences (```json ... ```) if present
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (```json or ```)
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].rstrip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse profile JSON: %s", raw_text[:200])
            data = {}

    if not isinstance(data, dict):
        data = {}

    profile = ApplicantProfile(
        session_id=session_id,
        filename=filename,
        is_relevant=bool(data.get("is_relevant", True)),
        document_type=_ensure_optional_str(data.get("document_type")),
        disciplines_of_interest=_ensure_str_list(data.get("disciplines_of_interest")),
        geographic_preferences=_ensure_str_list(data.get("geographic_preferences")),
        training_interests=_ensure_str_list(data.get("training_interests")),
        research_experience=_ensure_optional_str(data.get("research_experience")),
        clinical_experience=_ensure_optional_str(data.get("clinical_experience")),
        education=_ensure_optional_str(data.get("education")),
        languages=_ensure_str_list(data.get("languages")),
        career_goals=_ensure_optional_str(data.get("career_goals")),
        strengths=_ensure_str_list(data.get("strengths")),
        summary=_ensure_optional_str(data.get("summary")),
    )

    store_profile(profile)
    return profile


def format_profile_context(profile: ApplicantProfile) -> str:
    """Format profile as a context block to prepend to user messages."""
    parts = [f"[APPLICANT PROFILE — {profile.filename}]"]

    if profile.disciplines_of_interest:
        parts.append(f"Disciplines of interest: {', '.join(profile.disciplines_of_interest)}")
    if profile.geographic_preferences:
        parts.append(f"Geographic preferences: {', '.join(profile.geographic_preferences)}")
    if profile.training_interests:
        parts.append(f"Training interests: {', '.join(profile.training_interests)}")
    if profile.research_experience:
        parts.append(f"Research experience: {profile.research_experience}")
    if profile.clinical_experience:
        parts.append(f"Clinical experience: {profile.clinical_experience}")
    if profile.education:
        parts.append(f"Education: {profile.education}")
    if profile.languages:
        parts.append(f"Languages: {', '.join(profile.languages)}")
    if profile.career_goals:
        parts.append(f"Career goals: {profile.career_goals}")
    if profile.strengths:
        parts.append(f"Strengths: {', '.join(profile.strengths)}")
    if profile.summary:
        parts.append(f"Summary: {profile.summary}")

    parts.append("[END PROFILE]")
    return "\n".join(parts)
