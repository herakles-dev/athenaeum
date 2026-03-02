"""Semantic search across Alan Watts transcripts."""

import psycopg2
from fastapi import APIRouter, Query
from pydantic import BaseModel

from config.settings import DATABASE_URL
from src.embeddings.provider import embed_text

router = APIRouter()


class SearchResult(BaseModel):
    chunk_id: int
    transcript_id: int
    transcript_title: str
    series: str | None
    text: str
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


@router.get("/search", response_model=SearchResponse)
def semantic_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Semantic search across all Alan Watts content."""
    embedding = embed_text(q)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.transcript_id, t.title, t.series, c.text,
                       1 - (c.embedding <=> %s::vector) as similarity
                FROM chunks c
                JOIN transcripts t ON t.id = c.transcript_id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
            """, (str(embedding), str(embedding), limit))
            rows = cur.fetchall()
    finally:
        conn.close()

    results = [
        SearchResult(
            chunk_id=row[0],
            transcript_id=row[1],
            transcript_title=row[2],
            series=row[3],
            text=row[4],
            similarity=round(float(row[5]), 4)
        )
        for row in rows
    ]

    return SearchResponse(query=q, results=results, total=len(results))
