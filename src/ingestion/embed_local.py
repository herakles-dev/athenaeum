"""Generate embeddings locally using sentence-transformers (no API cost)."""

import os
import sys
import time

import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import DATABASE_URL

# all-mpnet-base-v2: 768 dims, best quality for sentence similarity
MODEL_NAME = "all-mpnet-base-v2"
EMBEDDING_DIMENSIONS = 768


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def embed_all_chunks(batch_size: int = 256):
    """Generate embeddings for all chunks using local model."""
    print(f"Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, text FROM chunks WHERE embedding IS NULL ORDER BY id"
            )
            unembedded = cur.fetchall()

        if not unembedded:
            print("All chunks already have embeddings.")
            return

        total = len(unembedded)
        print(f"Embedding {total} chunks in batches of {batch_size}...\n")
        done = 0
        start_time = time.time()

        for i in range(0, total, batch_size):
            batch = unembedded[i:i + batch_size]
            ids = [row[0] for row in batch]
            texts = [row[1] for row in batch]

            # Generate embeddings locally
            embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

            with conn.cursor() as cur:
                for chunk_id, emb in zip(ids, embeddings):
                    cur.execute(
                        "UPDATE chunks SET embedding = %s WHERE id = %s",
                        (emb.tolist(), chunk_id)
                    )
            conn.commit()

            done += len(batch)
            elapsed = time.time() - start_time
            rate = done / elapsed if elapsed > 0 else 0
            eta = (total - done) / rate if rate > 0 else 0
            print(f"  Embedded {done}/{total} chunks ({rate:.0f}/sec, ETA: {eta:.0f}s)")

        elapsed = time.time() - start_time
        print(f"\nDone. Embedded {total} chunks in {elapsed:.1f}s ({total/elapsed:.0f} chunks/sec)")

        # Verify
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
            embedded = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cur.fetchone()[0]
        print(f"Verification: {embedded}/{total_chunks} chunks have embeddings")

    finally:
        conn.close()


if __name__ == "__main__":
    embed_all_chunks()
