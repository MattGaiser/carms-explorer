"""Search service - semantic search via pgvector with filtering."""

from dataclasses import dataclass

from sqlalchemy import text
from sqlmodel import Session

from carms.search.embeddings import embed_query


@dataclass
class SearchResult:
    program_id: int
    program_name: str
    discipline: str
    school: str
    site: str
    stream: str
    chunk_text: str
    similarity: float
    url: str | None = None


class SearchService:
    """Semantic search over program embeddings."""

    def __init__(self, session: Session):
        self.session = session

    def search(
        self,
        query: str,
        top_k: int = 10,
        discipline_id: int | None = None,
        school_id: int | None = None,
        site: str | None = None,
    ) -> list[SearchResult]:
        """Embed query and find similar program chunks."""
        vector = embed_query(query)

        # Build WHERE clause
        conditions = []
        params: dict = {"embedding": str(vector), "top_k": top_k}

        if discipline_id is not None:
            conditions.append("p.discipline_id = :discipline_id")
            params["discipline_id"] = discipline_id
        if school_id is not None:
            conditions.append("p.school_id = :school_id")
            params["school_id"] = school_id
        if site is not None:
            conditions.append("LOWER(p.site) LIKE LOWER(:site)")
            params["site"] = f"%{site}%"

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        sql = text(f"""
            SELECT
                p.id AS program_id,
                p.name AS program_name,
                d.name AS discipline,
                s.name AS school,
                p.site,
                p.stream,
                pe.chunk_text,
                1 - (pe.embedding <=> CAST(:embedding AS vector)) AS similarity,
                p.url
            FROM program_embeddings pe
            JOIN programs p ON pe.program_id = p.id
            JOIN disciplines d ON p.discipline_id = d.id
            JOIN schools s ON p.school_id = s.id
            {where}
            ORDER BY pe.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)

        rows = self.session.execute(sql, params).fetchall()
        return [
            SearchResult(
                program_id=row[0],
                program_name=row[1],
                discipline=row[2],
                school=row[3],
                site=row[4],
                stream=row[5],
                chunk_text=row[6],
                similarity=float(row[7]),
                url=row[8],
            )
            for row in rows
        ]
