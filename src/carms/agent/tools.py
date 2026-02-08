"""Agent tools for CaRMS program exploration."""

import json
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool
from sqlalchemy import create_engine, text
from sqlmodel import Session

from carms.config import settings
from carms.search.embeddings import embed_query


def _get_session() -> Session:
    engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
    return Session(engine)


@tool(
    "search_programs",
    "Semantic search over CaRMS residency program descriptions."
    " Use this when a user describes what they're looking for.",
    {"query": str, "top_k": int},
)
async def search_programs(args: dict[str, Any]) -> dict[str, Any]:
    query = args["query"]
    top_k = args.get("top_k", 10)
    vector = embed_query(query)

    with _get_session() as session:
        rows = session.execute(
            text("""
                SELECT
                    p.id, p.name, d.name AS discipline, s.name AS school,
                    p.site, p.stream, pe.chunk_text,
                    1 - (pe.embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM program_embeddings pe
                JOIN programs p ON pe.program_id = p.id
                JOIN disciplines d ON p.discipline_id = d.id
                JOIN schools s ON p.school_id = s.id
                ORDER BY pe.embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """),
            {"embedding": str(vector), "top_k": top_k},
        ).fetchall()

    results = [
        {
            "program_id": row[0],
            "name": row[1],
            "discipline": row[2],
            "school": row[3],
            "site": row[4],
            "stream": row[5],
            "relevant_text": row[6][:300],
            "similarity": round(float(row[7]), 4),
        }
        for row in rows
    ]

    return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}


@tool(
    "filter_programs",
    "Filter programs by discipline, school, site, or stream. Use this for structured queries.",
    {"discipline": str, "school": str, "site": str, "stream": str},
)
async def filter_programs(args: dict[str, Any]) -> dict[str, Any]:
    conditions = []
    params: dict[str, Any] = {}

    if args.get("discipline"):
        conditions.append("LOWER(d.name) LIKE LOWER(:discipline)")
        params["discipline"] = f"%{args['discipline']}%"
    if args.get("school"):
        conditions.append("LOWER(s.name) LIKE LOWER(:school)")
        params["school"] = f"%{args['school']}%"
    if args.get("site"):
        conditions.append("LOWER(p.site) LIKE LOWER(:site)")
        params["site"] = f"%{args['site']}%"
    if args.get("stream"):
        conditions.append("LOWER(p.stream) LIKE LOWER(:stream)")
        params["stream"] = f"%{args['stream']}%"

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    with _get_session() as session:
        rows = session.execute(
            text(f"""
                SELECT p.id, p.name, d.name, s.name, p.site, p.stream
                FROM programs p
                JOIN disciplines d ON p.discipline_id = d.id
                JOIN schools s ON p.school_id = s.id
                {where}
                ORDER BY p.name
                LIMIT 50
            """),
            params,
        ).fetchall()

    results = [
        {
            "program_id": row[0],
            "name": row[1],
            "discipline": row[2],
            "school": row[3],
            "site": row[4],
            "stream": row[5],
        }
        for row in rows
    ]

    return {
        "content": [
            {
                "type": "text",
                "text": f"Found {len(results)} programs:\n{json.dumps(results, indent=2)}",
            }
        ]
    }


@tool(
    "get_program_detail",
    "Get full details for a specific program including all description sections.",
    {"program_id": int},
)
async def get_program_detail(args: dict[str, Any]) -> dict[str, Any]:
    program_id = args["program_id"]

    with _get_session() as session:
        row = session.execute(
            text("""
                SELECT p.name, d.name, s.name, p.site, p.stream, p.url,
                       pd.program_contacts, pd.general_instructions,
                       pd.supporting_documentation_information, pd.review_process,
                       pd.interviews, pd.selection_criteria, pd.program_highlights,
                       pd.program_curriculum, pd.training_sites,
                       pd.additional_information, pd.return_of_service
                FROM programs p
                JOIN disciplines d ON p.discipline_id = d.id
                JOIN schools s ON p.school_id = s.id
                LEFT JOIN program_descriptions pd ON pd.program_id = p.id
                WHERE p.id = :pid
            """),
            {"pid": program_id},
        ).first()

    if not row:
        return {"content": [{"type": "text", "text": f"Program {program_id} not found."}]}

    detail = {
        "name": row[0],
        "discipline": row[1],
        "school": row[2],
        "site": row[3],
        "stream": row[4],
        "url": row[5],
        "contacts": row[6],
        "general_instructions": row[7],
        "supporting_docs": row[8],
        "review_process": row[9],
        "interviews": row[10],
        "selection_criteria": row[11],
        "highlights": row[12],
        "curriculum": row[13],
        "training_sites": row[14],
        "additional_info": row[15],
        "return_of_service": row[16],
    }

    return {"content": [{"type": "text", "text": json.dumps(detail, indent=2, default=str)}]}


@tool(
    "compare_programs",
    "Compare multiple programs side by side. Provide a list of program IDs.",
    {"program_ids": str},
)
async def compare_programs(args: dict[str, Any]) -> dict[str, Any]:
    ids_str = args["program_ids"]
    try:
        program_ids = [int(x.strip()) for x in ids_str.split(",")]
    except ValueError:
        return {
            "content": [
                {"type": "text", "text": "Invalid program IDs. Provide comma-separated integers."}
            ]
        }

    with _get_session() as session:
        rows = session.execute(
            text("""
                SELECT p.id, p.name, d.name, s.name, p.site, p.stream,
                       pd.selection_criteria, pd.program_highlights, pd.interviews
                FROM programs p
                JOIN disciplines d ON p.discipline_id = d.id
                JOIN schools s ON p.school_id = s.id
                LEFT JOIN program_descriptions pd ON pd.program_id = p.id
                WHERE p.id = ANY(:ids)
                ORDER BY p.name
            """),
            {"ids": program_ids},
        ).fetchall()

    programs = []
    for row in rows:
        programs.append(
            {
                "program_id": row[0],
                "name": row[1],
                "discipline": row[2],
                "school": row[3],
                "site": row[4],
                "stream": row[5],
                "selection_criteria": (row[6] or "")[:500],
                "highlights": (row[7] or "")[:500],
                "interviews": (row[8] or "")[:500],
            }
        )

    return {"content": [{"type": "text", "text": json.dumps(programs, indent=2, default=str)}]}


@tool(
    "list_disciplines",
    "List all 37 medical disciplines with program counts.",
    {},
)
async def list_disciplines(args: dict[str, Any]) -> dict[str, Any]:
    with _get_session() as session:
        rows = session.execute(
            text("""
                SELECT d.id, d.name, COUNT(p.id) AS cnt
                FROM disciplines d
                LEFT JOIN programs p ON d.id = p.discipline_id
                GROUP BY d.id, d.name
                ORDER BY d.name
            """)
        ).fetchall()

    results = [{"id": row[0], "name": row[1], "program_count": row[2]} for row in rows]
    return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}


@tool(
    "list_schools",
    "List all Canadian medical schools with program counts.",
    {},
)
async def list_schools(args: dict[str, Any]) -> dict[str, Any]:
    with _get_session() as session:
        rows = session.execute(
            text("""
                SELECT s.id, s.name, COUNT(p.id) AS cnt
                FROM schools s
                LEFT JOIN programs p ON s.id = p.school_id
                GROUP BY s.id, s.name
                ORDER BY cnt DESC
            """)
        ).fetchall()

    results = [{"id": row[0], "name": row[1], "program_count": row[2]} for row in rows]
    return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}


@tool(
    "get_analytics",
    "Get aggregate statistics about CaRMS programs.",
    {},
)
async def get_analytics(args: dict[str, Any]) -> dict[str, Any]:
    with _get_session() as session:
        stats = {}
        stats["total_programs"] = session.execute(text("SELECT COUNT(*) FROM programs")).scalar()
        stats["total_disciplines"] = session.execute(
            text("SELECT COUNT(*) FROM disciplines")
        ).scalar()
        stats["total_schools"] = session.execute(text("SELECT COUNT(*) FROM schools")).scalar()

        top_disciplines = session.execute(
            text("""
                SELECT d.name, COUNT(*) AS cnt
                FROM programs p JOIN disciplines d ON p.discipline_id = d.id
                GROUP BY d.name ORDER BY cnt DESC LIMIT 10
            """)
        ).fetchall()
        stats["top_disciplines"] = [{"name": r[0], "count": r[1]} for r in top_disciplines]

        top_sites = session.execute(
            text("""
                SELECT site, COUNT(*) AS cnt
                FROM programs GROUP BY site ORDER BY cnt DESC LIMIT 10
            """)
        ).fetchall()
        stats["top_sites"] = [{"site": r[0], "count": r[1]} for r in top_sites]

    return {"content": [{"type": "text", "text": json.dumps(stats, indent=2)}]}


# Create MCP server with all tools
carms_mcp_server = create_sdk_mcp_server(
    name="carms",
    version="1.0.0",
    tools=[
        search_programs,
        filter_programs,
        get_program_detail,
        compare_programs,
        list_disciplines,
        list_schools,
        get_analytics,
    ],
)
