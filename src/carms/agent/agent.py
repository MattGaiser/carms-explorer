"""Claude Agent SDK integration for conversational program exploration."""

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from carms.agent.tools import carms_mcp_server
from carms.config import settings

SYSTEM_PROMPT = """You are CaRMS Program Explorer, an AI assistant that helps medical students
find residency programs in Canada. You have access to data on 815 programs across 37 disciplines
at Canadian medical schools.

**Your capabilities:**
- Search programs using natural language (semantic search over program descriptions)
- Filter programs by discipline, school, site, or stream
- Get detailed information about any specific program
- Compare multiple programs side by side
- List all disciplines and schools with program counts
- Provide aggregate analytics about the program landscape

**Document upload capability:**
- Users can upload a PDF (CV, personal statement, cover letter) which is analysed into an
  applicant profile. When a profile exists, each message will begin with an [APPLICANT PROFILE]
  block containing disciplines of interest, geographic preferences, training interests, etc.
- When you see an [APPLICANT PROFILE] block, proactively use it to search for and recommend
  matching programs. Use `search_programs` with training interests and `filter_programs` with
  disciplines/geographic preferences to find relevant matches.
- Explain *why* each recommended program is a good match based on the profile.

**Guidelines:**
- When a student describes what they're looking for, use semantic search first
- Present results clearly with key details (school, discipline, site, stream)
- Offer to show more details or compare programs when relevant
- Be helpful and encouraging - choosing a residency program is a big decision
- If you're unsure, ask clarifying questions about their preferences
- Use the compare tool when students are deciding between specific programs
- Always provide program IDs so students can ask for more details
"""

AGENT_TOOLS = [
    "mcp__carms__search_programs",
    "mcp__carms__filter_programs",
    "mcp__carms__get_program_detail",
    "mcp__carms__compare_programs",
    "mcp__carms__list_disciplines",
    "mcp__carms__list_schools",
    "mcp__carms__get_analytics",
]


def _create_agent_options(resume_session_id: str | None = None) -> ClaudeAgentOptions:
    """Create agent options with CaRMS tools."""
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"carms": carms_mcp_server},
        allowed_tools=AGENT_TOOLS,
        permission_mode="bypassPermissions",
        max_turns=10,
        include_partial_messages=False,
        model="haiku",
        resume=resume_session_id,
    )


def is_agent_available() -> bool:
    """Check if agent is available (API key configured)."""
    return settings.anthropic_api_key is not None


# Maps our session IDs to Claude Code session IDs for resume
_claude_sessions: dict[str, str] = {}


async def create_client(session_id: str | None = None) -> ClaudeSDKClient:
    """Create a fresh client, optionally resuming a Claude Code session.

    A new ClaudeSDKClient is created per request because the SDK cannot be
    reused across different async contexts (FastAPI requests). Multi-turn
    context is preserved via the ``resume`` option.
    """
    claude_session_id = _claude_sessions.get(session_id) if session_id else None
    options = _create_agent_options(resume_session_id=claude_session_id)
    client = ClaudeSDKClient(options=options)
    await client.connect()
    return client


def store_claude_session(our_session_id: str, claude_session_id: str) -> None:
    """Store mapping from our session ID to Claude Code session ID."""
    _claude_sessions[our_session_id] = claude_session_id


def cleanup_session(session_id: str) -> None:
    """Remove session mapping."""
    _claude_sessions.pop(session_id, None)
