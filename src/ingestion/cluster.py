"""Auto-discover topics from chunk embeddings using K-Means + keyword extraction."""

import json
import os
import re
import sys
from collections import Counter

import numpy as np
import psycopg2
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import DATABASE_URL, LIB


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def load_embeddings(conn) -> tuple[list[int], np.ndarray, list[str], list[int]]:
    """Load all chunk embeddings from the database."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.embedding::text, c.text, c.transcript_id
            FROM chunks c
            WHERE c.embedding IS NOT NULL
            ORDER BY c.id
        """)
        rows = cur.fetchall()

    chunk_ids = []
    embeddings = []
    texts = []
    transcript_ids = []

    for row in rows:
        chunk_ids.append(row[0])
        vec_str = row[1].strip("[]")
        vec = [float(x) for x in vec_str.split(",")]
        embeddings.append(vec)
        texts.append(row[2])
        transcript_ids.append(row[3])

    return chunk_ids, np.array(embeddings), texts, transcript_ids


def find_optimal_k(embeddings: np.ndarray, k_range: range = range(8, 25)) -> int:
    """Find optimal number of clusters using silhouette score."""
    print("  Finding optimal k...")
    best_k = 15
    best_score = -1

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = km.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels, sample_size=2000, random_state=42)
        print(f"    k={k}: silhouette={score:.4f}")
        if score > best_score:
            best_score = score
            best_k = k

    print(f"  Best k={best_k} (silhouette={best_score:.4f})")
    return best_k


def cluster_embeddings(embeddings: np.ndarray, n_clusters: int = None) -> tuple[np.ndarray, np.ndarray]:
    """Run K-Means clustering on embeddings."""
    if n_clusters is None:
        n_clusters = find_optimal_k(embeddings)

    print(f"  K-Means: k={n_clusters}")
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    labels = km.fit_predict(embeddings)
    centers = km.cluster_centers_

    score = silhouette_score(embeddings, labels, sample_size=2000, random_state=42)
    print(f"  Silhouette score: {score:.4f}")

    return labels, centers


STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "between", "out", "off", "over", "under",
    "again", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "now", "and", "but", "or", "if", "while",
    "because", "about", "that", "this", "these", "those", "what", "which",
    "who", "whom", "it", "its", "he", "she", "they", "them", "his", "her",
    "their", "we", "us", "our", "you", "your", "me", "my", "myself",
    "going", "get", "got", "thing", "things", "say", "said", "know",
    "like", "really", "see", "well", "one", "way", "something", "don",
    "mean", "people", "right", "come", "think", "make", "take", "much",
    "want", "look", "give", "back", "also", "even", "new", "first",
    "let", "put", "go", "call", "called", "always", "every", "still",
    "whole", "anything", "nothing", "everything", "alan", "watts",
    "course", "sort", "quite", "rather", "whether", "therefore",
    "point", "view", "simply", "certainly", "perhaps", "however",
    "little", "bit", "great", "deal", "kind", "tell", "fact",
    "begin", "already", "understand", "talk", "two", "three",
    "keep", "find", "long", "use", "many", "part", "another",
    "different", "place", "end", "hand", "else", "seems", "trying",
    "saying", "really", "idea", "sense", "time", "actually", "man",
}


def extract_keywords(texts: list[str], top_n: int = 20) -> list[str]:
    """Extract distinguishing keywords from cluster texts."""
    words = Counter()
    bigrams = Counter()

    for text in texts:
        text_words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        filtered = [w for w in text_words if w not in STOPWORDS]
        words.update(filtered)
        for i in range(len(filtered) - 1):
            bigrams[f"{filtered[i]} {filtered[i+1]}"] += 1

    top_bigrams = [b for b, c in bigrams.most_common(15) if c >= 5]
    top_words = [w for w, _ in words.most_common(top_n)]
    return top_bigrams[:5] + top_words[:top_n - 5]


def label_topic(keywords: list[str], sample_texts: list[str]) -> str:
    """Generate a topic label from keywords using scored matching.

    Uses fine-grained rules from library.yml ordered from most specific to broadest.
    Each cluster gets scored against all rules; the highest-scoring rule wins.
    """
    kw_str = " ".join(keywords).lower()

    # Load rules from library config (triggers, label, weight tuples)
    rules = [rule.as_tuple() for rule in LIB.topic_rules]

    # Score each rule
    best_label = None
    best_score = 0

    for triggers, label, bonus in rules:
        matches = sum(1 for t in triggers if t in kw_str)
        score = matches * bonus
        if score > best_score:
            best_score = score
            best_label = label

    if best_label and best_score >= 1.5:
        return best_label

    # Last resort: capitalize top keywords
    clean = [k for k in keywords[:4] if len(k) > 3]
    return " & ".join(w.title() for w in clean[:3])


def store_topics(conn, cluster_data: list[dict]):
    """Store discovered topics in the database."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM transcript_topics")
        cur.execute("DELETE FROM topics")

        for cluster in cluster_data:
            cur.execute(
                "INSERT INTO topics (name, description) VALUES (%s, %s) RETURNING id",
                (cluster["label"], json.dumps({
                    "keywords": cluster["keywords"],
                    "chunk_count": int(cluster["chunk_count"]),
                    "transcript_count": int(cluster["transcript_count"]),
                }))
            )
            topic_id = cur.fetchone()[0]

            for tid, score in cluster["transcript_scores"].items():
                cur.execute(
                    "INSERT INTO transcript_topics (transcript_id, topic_id, relevance_score) "
                    "VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (int(tid), topic_id, float(score))
                )

    conn.commit()


def run():
    conn = get_connection()
    try:
        print("=== Loading embeddings ===\n")
        chunk_ids, embeddings, texts, transcript_ids = load_embeddings(conn)
        print(f"Loaded {len(chunk_ids)} chunk embeddings\n")

        print("=== Clustering ===\n")
        labels, centers = cluster_embeddings(embeddings, n_clusters=15)

        print("\n=== Analyzing clusters ===\n")
        cluster_data = []
        n_clusters = len(set(labels))

        for cluster_id in range(n_clusters):
            mask = labels == cluster_id
            cluster_texts = [texts[i] for i in range(len(texts)) if mask[i]]
            cluster_tids = [transcript_ids[i] for i in range(len(transcript_ids)) if mask[i]]

            keywords = extract_keywords(cluster_texts)
            topic_label = label_topic(keywords, cluster_texts[:5])

            # Transcript relevance scores
            tid_counts = Counter(cluster_tids)
            unique_tids = set(cluster_tids)
            transcript_scores = {}

            with conn.cursor() as cur:
                for tid in unique_tids:
                    cur.execute("SELECT COUNT(*) FROM chunks WHERE transcript_id = %s", (tid,))
                    total = cur.fetchone()[0]
                    transcript_scores[tid] = round(tid_counts[tid] / max(total, 1), 3)

            cluster_info = {
                "cluster_id": int(cluster_id),
                "label": topic_label,
                "keywords": keywords[:10],
                "chunk_count": int(sum(mask)),
                "transcript_count": len(unique_tids),
                "transcript_scores": transcript_scores,
            }
            cluster_data.append(cluster_info)

            print(f"  [{cluster_id:2d}] \"{topic_label}\"")
            print(f"      {sum(mask)} chunks, {len(unique_tids)} transcripts")
            print(f"      Keywords: {', '.join(keywords[:8])}")
            print()

        # Deduplicate labels — use distinguishing keywords instead of numbers
        seen_labels = {}
        for cd in cluster_data:
            base = cd["label"]
            if base in seen_labels:
                seen_labels[base] += 1
                # Find keywords unique to this cluster vs others with same label
                other_kw = set()
                for other in cluster_data:
                    if other["label"] == base and other is not cd:
                        other_kw.update(other["keywords"][:5])
                unique_kw = [k for k in cd["keywords"][:6]
                             if k not in other_kw and len(k) > 3]
                if unique_kw:
                    suffix = unique_kw[0].title()
                    cd["label"] = f"{base}: {suffix}"
                else:
                    cd["label"] = f"{base} ({seen_labels[base]})"
            else:
                seen_labels[base] = 1

        print(f"=== Storing {len(cluster_data)} topics ===\n")
        store_topics(conn, cluster_data)

        # Final summary
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.name, COUNT(tt.transcript_id) as transcripts,
                       t.description::json->>'chunk_count' as chunks
                FROM topics t
                LEFT JOIN transcript_topics tt ON tt.topic_id = t.id
                GROUP BY t.id, t.name, t.description
                ORDER BY (t.description::json->>'chunk_count')::int DESC
            """)
            rows = cur.fetchall()

        print("=== Topic Map ===\n")
        for name, n_trans, n_chunks in rows:
            bar = "#" * (int(n_chunks) // 20)
            print(f"  {name:40s} {n_chunks:>4s} chunks  {n_trans:>3d} transcripts  {bar}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
