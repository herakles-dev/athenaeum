"""Load transcripts from local data sources into PostgreSQL.

TODO: Implement the data loading functions below for your corpus.
      The scaffold provides helpers for DB connection, SHA-256 dedup,
      and transcript insertion — just implement your source-specific loaders.

IMPORTANT: Run with `make run-pipeline` or:
    PYTHONPATH=. python3 -c "from src.ingestion.loader import run; run()"
"""

import hashlib
import json
import os
import re
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import DATABASE_URL, DATA_DIR


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def content_hash(text: str) -> str:
    """SHA-256 hash for deduplication. Normalized (whitespace collapsed, lowercase)."""
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()


def ensure_source(conn, name: str, url: str, source_type: str) -> int:
    """Get or create a source record. Returns source_id."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO sources (name, url, source_type, scraped_at) "
            "VALUES (%s, %s, %s, NOW()) RETURNING id",
            (name, url, source_type)
        )
        conn.commit()
        return cur.fetchone()[0]


def insert_transcript(conn, source_id: int, title: str, full_text: str,
                      series: str = None, source_url: str = None,
                      video_url: str = None, metadata: dict = None) -> int | None:
    """Insert a transcript, skipping if duplicate (by content hash).

    Returns the new transcript ID, or None if it was a duplicate.
    """
    h = content_hash(full_text)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM transcripts WHERE content_hash = %s", (h,))
        if cur.fetchone():
            return None  # duplicate — safe to skip
        cur.execute(
            "INSERT INTO transcripts "
            "(source_id, title, series, full_text, content_hash, source_url, video_url, metadata) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (source_id, title, series, full_text, h, source_url, video_url,
             json.dumps(metadata or {}))
        )
        conn.commit()
        return cur.fetchone()[0]


# ── TODO: Implement your data loaders below ───────────────────────────────────

def load_my_source(conn):
    """TODO: Load transcripts from your primary data source.

    Example: loading from JSON files in data/my-source/
    """
    # TODO: Set this to where your data lives
    data_path = Path(DATA_DIR) / "TODO-your-data-dir"

    if not data_path.exists():
        print(f"[SKIP] {data_path} not found. Add your data to data/")
        return

    # Register your source
    source_id = ensure_source(
        conn,
        "TODO Source Name",           # Human-readable source name
        "https://TODO-source-url",    # URL to source (can be empty string)
        "TODO"                        # Type: github | scraped | manual | ...
    )

    inserted = 0
    skipped = 0

    # TODO: Iterate your files and call insert_transcript for each
    # Example for JSON files:
    # for json_file in sorted(data_path.glob("*.json")):
    #     with open(json_file) as f:
    #         data = json.load(f)
    #     tid = insert_transcript(
    #         conn,
    #         source_id=source_id,
    #         title=data["title"],
    #         full_text=data["text"],           # The actual transcript text
    #         series=data.get("series"),        # Optional grouping/series name
    #         source_url=data.get("url"),       # Original URL if available
    #         video_url=data.get("video_url"),  # YouTube URL if available
    #         metadata={"key": data.get("key")} # Any extra metadata as dict
    #     )
    #     if tid:
    #         inserted += 1
    #     else:
    #         skipped += 1

    print(f"[TODO Source] Inserted: {inserted}, Skipped (dupes): {skipped}")


# ── Optional: add more loaders here for additional sources ────────────────────
# def load_another_source(conn): ...


# ── run() — called by make run-pipeline ──────────────────────────────────────

def run():
    """Load all data sources."""
    conn = get_connection()
    try:
        print("=== Loading transcripts ===\n")

        # TODO: Call your loader functions here
        load_my_source(conn)
        # load_another_source(conn)

        # Summary
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transcripts")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM sources")
            sources_count = cur.fetchone()[0]
            cur.execute("SELECT SUM(LENGTH(full_text)) FROM transcripts")
            chars = cur.fetchone()[0] or 0

        print(f"\n=== Summary ===")
        print(f"Sources: {sources_count}")
        print(f"Transcripts: {total}")
        print(f"Total characters: {chars:,}")
        print(f"Estimated words: {chars // 5:,}")
    finally:
        conn.close()


# Keep backward compat with older pipeline call
load_all = run

if __name__ == "__main__":
    run()
