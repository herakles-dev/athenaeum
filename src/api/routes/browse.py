"""Browse transcripts by series, title, or full text."""

import psycopg2
from fastapi import APIRouter, Query
from pydantic import BaseModel

from config.settings import DATABASE_URL

router = APIRouter()


class TranscriptSummary(BaseModel):
    id: int
    title: str
    series: str | None
    source: str
    word_count: int


class TranscriptDetail(BaseModel):
    id: int
    title: str
    series: str | None
    full_text: str
    source: str
    source_url: str | None
    video_url: str | None


class SeriesInfo(BaseModel):
    series: str
    count: int


class TopicSummary(BaseModel):
    id: int
    name: str
    chunk_count: int
    transcript_count: int
    keywords: list[str]


class TopicDetail(BaseModel):
    id: int
    name: str
    chunk_count: int
    transcript_count: int
    keywords: list[str]
    transcripts: list[TranscriptSummary]


@router.get("/transcripts", response_model=list[TranscriptSummary])
def list_transcripts(
    series: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List transcripts with optional filtering."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            conditions = []
            params = []

            if series:
                conditions.append("t.series = %s")
                params.append(series)
            if search:
                conditions.append("(t.title ILIKE %s OR t.full_text ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            where = "WHERE " + " AND ".join(conditions) if conditions else ""
            params.extend([limit, offset])

            cur.execute(f"""
                SELECT t.id, t.title, t.series, s.name,
                       LENGTH(t.full_text) / 5 as word_count
                FROM transcripts t
                JOIN sources s ON s.id = t.source_id
                {where}
                ORDER BY t.series, t.title
                LIMIT %s OFFSET %s
            """, params)
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        TranscriptSummary(
            id=row[0], title=row[1], series=row[2],
            source=row[3], word_count=row[4]
        )
        for row in rows
    ]


@router.get("/transcripts/{transcript_id}", response_model=TranscriptDetail)
def get_transcript(transcript_id: int):
    """Get full transcript text."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.id, t.title, t.series, t.full_text,
                       s.name, t.source_url, t.video_url
                FROM transcripts t
                JOIN sources s ON s.id = t.source_id
                WHERE t.id = %s
            """, (transcript_id,))
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transcript not found")

    return TranscriptDetail(
        id=row[0], title=row[1], series=row[2], full_text=row[3],
        source=row[4], source_url=row[5], video_url=row[6]
    )


@router.get("/series", response_model=list[SeriesInfo])
def list_series():
    """List all series with transcript counts."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT series, COUNT(*) as cnt
                FROM transcripts
                WHERE series IS NOT NULL
                GROUP BY series
                ORDER BY series
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    return [SeriesInfo(series=row[0], count=row[1]) for row in rows]


@router.get("/topics", response_model=list[TopicSummary])
def list_topics():
    """List all auto-discovered topics with chunk/transcript counts."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.id, t.name, t.description,
                       COUNT(tt.transcript_id) as transcript_count
                FROM topics t
                LEFT JOIN transcript_topics tt ON tt.topic_id = t.id
                GROUP BY t.id, t.name, t.description
                ORDER BY (t.description::json->>'chunk_count')::int DESC
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    import json
    results = []
    for row in rows:
        desc = json.loads(row[2]) if row[2] else {}
        results.append(TopicSummary(
            id=row[0],
            name=row[1],
            chunk_count=desc.get("chunk_count", 0),
            transcript_count=int(row[3]),
            keywords=desc.get("keywords", []),
        ))
    return results


@router.get("/topics/{topic_id}", response_model=TopicDetail)
def get_topic(topic_id: int):
    """Get topic details with its associated transcripts."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM topics WHERE id = %s", (topic_id,))
            topic_row = cur.fetchone()
            if not topic_row:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Topic not found")

            cur.execute("""
                SELECT t.id, t.title, t.series, s.name,
                       LENGTH(t.full_text) / 5 as word_count,
                       tt.relevance_score
                FROM transcript_topics tt
                JOIN transcripts t ON t.id = tt.transcript_id
                JOIN sources s ON s.id = t.source_id
                WHERE tt.topic_id = %s
                ORDER BY tt.relevance_score DESC
                LIMIT 50
            """, (topic_id,))
            transcript_rows = cur.fetchall()
    finally:
        conn.close()

    import json
    desc = json.loads(topic_row[2]) if topic_row[2] else {}

    transcripts = [
        TranscriptSummary(
            id=row[0], title=row[1], series=row[2],
            source=row[3], word_count=row[4]
        )
        for row in transcript_rows
    ]

    return TopicDetail(
        id=topic_row[0],
        name=topic_row[1],
        chunk_count=desc.get("chunk_count", 0),
        transcript_count=desc.get("transcript_count", 0),
        keywords=desc.get("keywords", []),
        transcripts=transcripts,
    )
