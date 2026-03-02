"""Generate embeddings for transcript chunks and store in pgvector."""

import os
import sys
import time

import psycopg2
from google import genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import DATABASE_URL
from src.ingestion.chunker import chunk_text

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


def chunk_and_store(conn, transcript_id: int, full_text: str):
    """Chunk a transcript and insert chunks (without embeddings yet)."""
    chunks = chunk_text(full_text)
    with conn.cursor() as cur:
        for chunk in chunks:
            cur.execute(
                "INSERT INTO chunks (transcript_id, chunk_index, text, token_count) "
                "VALUES (%s, %s, %s, %s)",
                (transcript_id, chunk["chunk_index"], chunk["text"], chunk["token_count"])
            )
    conn.commit()
    return len(chunks)


def chunk_all_transcripts(conn):
    """Create chunks for all transcripts that don't have chunks yet."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT t.id, t.title, t.full_text FROM transcripts t "
            "WHERE NOT EXISTS (SELECT 1 FROM chunks c WHERE c.transcript_id = t.id) "
            "ORDER BY t.id"
        )
        transcripts = cur.fetchall()

    total_chunks = 0
    for tid, title, full_text in transcripts:
        n = chunk_and_store(conn, tid, full_text)
        total_chunks += n
        print(f"  [{tid}] {title}: {n} chunks")

    print(f"\nTotal new chunks: {total_chunks}")
    return total_chunks


def embed_batch(client, texts: list[str]) -> list[list[float]]:
    """Get embeddings for a batch of texts using Gemini."""
    from google.genai import types
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return [e.values for e in result.embeddings]


def embed_all_chunks(conn, batch_size: int = 50):
    """Generate embeddings for all chunks that don't have them yet."""
    client = get_gemini_client()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, text FROM chunks WHERE embedding IS NULL ORDER BY id"
        )
        unembedded = cur.fetchall()

    if not unembedded:
        print("All chunks already have embeddings.")
        return

    print(f"Embedding {len(unembedded)} chunks in batches of {batch_size}...")
    total = len(unembedded)
    done = 0

    for i in range(0, total, batch_size):
        batch = unembedded[i:i + batch_size]
        ids = [row[0] for row in batch]
        texts = [row[1] for row in batch]

        try:
            embeddings = embed_batch(client, texts)
        except Exception as e:
            print(f"  Error at batch {i}: {e}")
            # Retry with smaller batch
            time.sleep(5)
            try:
                embeddings = embed_batch(client, texts)
            except Exception as e2:
                print(f"  Retry failed: {e2}, skipping batch")
                continue

        with conn.cursor() as cur:
            for chunk_id, emb in zip(ids, embeddings):
                cur.execute(
                    "UPDATE chunks SET embedding = %s WHERE id = %s",
                    (str(emb), chunk_id)
                )
        conn.commit()

        done += len(batch)
        print(f"  Embedded {done}/{total} chunks")

        # Gemini free tier: 1500 RPM, but be courteous
        if i + batch_size < total:
            time.sleep(1)

    print(f"\nDone. Embedded {done} chunks.")


def run():
    conn = get_connection()
    try:
        print("=== Phase 1: Chunking transcripts ===\n")
        chunk_all_transcripts(conn)

        print("\n=== Phase 2: Generating embeddings (Gemini) ===\n")
        embed_all_chunks(conn)

        # Summary
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
            embedded = cur.fetchone()[0]
            cur.execute("SELECT SUM(token_count) FROM chunks")
            total_tokens = cur.fetchone()[0] or 0

        print(f"\n=== Summary ===")
        print(f"Total chunks: {total_chunks}")
        print(f"Embedded: {embedded}")
        print(f"Total tokens: {total_tokens:,}")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
