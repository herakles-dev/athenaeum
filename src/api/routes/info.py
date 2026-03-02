"""Library info endpoint — metadata + live corpus counts."""

import psycopg2
from fastapi import APIRouter

from config.settings import DATABASE_URL, LIB

router = APIRouter()


def _get_corpus_counts() -> dict:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transcripts")
            transcript_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
            chunk_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM topics")
            topic_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT series) FROM transcripts WHERE series IS NOT NULL AND series != ''")
            series_count = cur.fetchone()[0]
    finally:
        conn.close()

    return {
        "transcript_count": transcript_count,
        "chunk_count": chunk_count,
        "topic_count": topic_count,
        "series_count": series_count,
    }


@router.get("/info")
def get_info():
    """Return library metadata, live corpus counts, and frontend config."""
    lib = LIB.library
    fe = LIB.frontend

    corpus = _get_corpus_counts()

    return {
        "library": {
            "name": lib.name,
            "title": lib.title,
            "author": lib.author,
            "domain": lib.domain,
            "description": lib.description,
        },
        "corpus": corpus,
        "frontend": {
            "suggestions": fe.suggestions,
            "heroTagline": fe.hero_tagline,
            "accentColor": fe.accent_color,
        },
    }
