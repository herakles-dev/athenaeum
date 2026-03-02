"""Ingestion pipeline smoke tests (unit-level, no DB required for most).

Run:  pytest tests/test_ingestion.py -v
"""

import pytest


# ── Chunker ─────────────────────────────────────────────────────────────


def test_chunker_import():
    from src.ingestion.chunker import chunk_text
    chunks = chunk_text("Alan Watts once said " * 100, chunk_size=50, overlap=5)
    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)


def test_chunker_respects_overlap():
    from src.ingestion.chunker import chunk_text
    text = " ".join([f"word{i}" for i in range(200)])
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    # Overlap means consecutive chunks share tokens
    assert len(chunks) >= 3


# ── Embeddings ──────────────────────────────────────────────────────────


def test_embedding_provider_loads():
    from src.embeddings.provider import get_embedder
    embedder = get_embedder()
    assert embedder is not None


def test_embedding_dimensions():
    from src.embeddings.provider import get_embedder
    embedder = get_embedder()
    vec = embedder.encode("what is consciousness?")
    assert vec.shape == (768,)


# ── LLM Provider ────────────────────────────────────────────────────────


def test_llm_provider_factory_openrouter():
    import os
    os.environ.setdefault("LLM_PROVIDER", "openrouter")
    from src.llm.provider import get_provider
    provider = get_provider()
    assert provider is not None
