import os

from config.library_config import get_library_config

LIB = get_library_config()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql://alan_watts:{os.environ.get('ALAN_WATTS_DB_PASSWORD', '')}@127.0.0.1:5441/alan_watts"
)

# Legacy API keys (kept for embedding pipeline compatibility)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Pluggable LLM provider for chat
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")   # anthropic | openai | ollama
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")

EMBEDDING_MODEL = "all-mpnet-base-v2"  # Local sentence-transformers model
EMBEDDING_DIMENSIONS = 768

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
TRANSCRIPTS_DIR = os.path.join(DATA_DIR, "transcripts")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
