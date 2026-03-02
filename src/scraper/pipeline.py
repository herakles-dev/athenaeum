"""Orchestrate all scrapers and load results into the database."""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.scraper.deoxy import scrape_all as scrape_deoxy
from src.scraper.youtube import extract_all as extract_youtube
from src.ingestion.loader import get_connection, ensure_source, insert_transcript


def import_deoxy(conn):
    """Import deoxy.org essays."""
    print("\n=== Scraping deoxy.org mirror ===\n")
    results = scrape_deoxy()

    if not results:
        print("No results from deoxy.org")
        return

    source_id = ensure_source(
        conn,
        "Deoxy.org Mirror",
        "https://www.jacobsm.com/deoxy/deoxy.org/watts.htm",
        "website"
    )

    inserted = 0
    skipped = 0
    for r in results:
        tid = insert_transcript(
            conn,
            source_id=source_id,
            title=r["title"],
            full_text=r["text"],
            source_url=r["url"],
            metadata={"source_path": r["source_path"]}
        )
        if tid:
            inserted += 1
        else:
            skipped += 1

    print(f"\n[Deoxy.org] Inserted: {inserted}, Skipped (dupes): {skipped}")


def import_youtube(conn, max_videos: int = 500):
    """Import YouTube transcripts."""
    print("\n=== Extracting YouTube transcripts ===\n")
    results = extract_youtube(max_videos=max_videos)

    if not results:
        print("No results from YouTube")
        return

    source_id = ensure_source(
        conn,
        "YouTube Official Channel",
        "https://www.youtube.com/@AlanWattsOrg",
        "youtube"
    )

    inserted = 0
    skipped = 0
    for r in results:
        tid = insert_transcript(
            conn,
            source_id=source_id,
            title=r["title"],
            full_text=r["text"],
            video_url=r["url"],
            metadata={"video_id": r["video_id"], "method": r["method"]}
        )
        if tid:
            inserted += 1
        else:
            skipped += 1

    print(f"\n[YouTube] Inserted: {inserted}, Skipped (dupes): {skipped}")


def run(youtube_max: int = 500):
    conn = get_connection()
    try:
        import_deoxy(conn)
        import_youtube(conn, max_videos=youtube_max)

        # Summary
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.name, COUNT(t.id) as cnt, SUM(LENGTH(t.full_text)) as chars
                FROM sources s
                LEFT JOIN transcripts t ON t.source_id = s.id
                GROUP BY s.name
                ORDER BY s.name
            """)
            rows = cur.fetchall()

        print(f"\n=== Final Summary ===")
        total_t = 0
        total_c = 0
        for name, cnt, chars in rows:
            chars = chars or 0
            print(f"  {name}: {cnt} transcripts, {chars:,} chars")
            total_t += cnt
            total_c += chars
        print(f"  TOTAL: {total_t} transcripts, {total_c:,} chars (~{total_c // 5:,} words)")
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--youtube-max", type=int, default=500)
    args = parser.parse_args()
    run(youtube_max=args.youtube_max)
