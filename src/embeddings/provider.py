"""Shared embedding provider using local sentence-transformers model."""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-mpnet-base-v2"
EMBEDDING_DIMENSIONS = 768

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    model = get_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple text strings."""
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return [e.tolist() for e in embeddings]
