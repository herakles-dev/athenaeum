"""API endpoint smoke tests.

Run:  pytest tests/test_api.py -v
Req:  docker compose up -d db api   (live DB required)
"""

import pytest
import httpx


BASE = "http://127.0.0.1:8131"


# ── Health ──────────────────────────────────────────────────────────────


def test_health():
    r = httpx.get(f"{BASE}/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["service"] == "alan-watts-library"


# ── Search ──────────────────────────────────────────────────────────────


def test_search_returns_results():
    r = httpx.get(f"{BASE}/api/search", params={"q": "ego", "limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    assert len(body["results"]) > 0


def test_search_result_shape():
    r = httpx.get(f"{BASE}/api/search", params={"q": "wu wei", "limit": 3})
    result = r.json()["results"][0]
    assert "chunk_id" in result
    assert "transcript_title" in result
    assert "text" in result
    assert 0.0 <= result["similarity"] <= 1.0


def test_search_empty_query():
    r = httpx.get(f"{BASE}/api/search", params={"q": "", "limit": 5})
    # Should return 422 or empty results — not 500
    assert r.status_code in (200, 422)


# ── Browse ──────────────────────────────────────────────────────────────


def test_transcripts_list():
    r = httpx.get(f"{BASE}/api/transcripts")
    assert r.status_code == 200
    body = r.json()
    assert "transcripts" in body
    assert len(body["transcripts"]) >= 100


def test_transcripts_filter_by_series():
    r = httpx.get(f"{BASE}/api/transcripts", params={"series": "Tao"})
    assert r.status_code == 200


def test_transcript_detail():
    r = httpx.get(f"{BASE}/api/transcripts/1")
    assert r.status_code == 200
    body = r.json()
    assert "title" in body
    assert "full_text" in body


def test_series_list():
    r = httpx.get(f"{BASE}/api/series")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_topics_list():
    r = httpx.get(f"{BASE}/api/topics")
    assert r.status_code == 200
    topics = r.json()
    assert len(topics) == 15


def test_topic_detail():
    r = httpx.get(f"{BASE}/api/topics/1")
    assert r.status_code == 200
    body = r.json()
    assert "name" in body


# ── Settings ────────────────────────────────────────────────────────────


def test_settings_get():
    r = httpx.get(f"{BASE}/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert "provider" in body
