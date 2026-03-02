"""RAG chat endpoint - Talk to Alan Watts."""

import os
import psycopg2
from fastapi import APIRouter
from pydantic import BaseModel

from config.settings import DATABASE_URL, LIB
from src.embeddings.provider import embed_text
from fastapi import HTTPException
from src.llm.provider import get_provider, AnthropicProvider, OpenAIProvider, OllamaProvider, GeminiProvider, OpenRouterProvider

router = APIRouter()

ALAN_WATTS_SYSTEM_PROMPT = LIB.rag_persona.build_system_prompt()


class ChatRequest(BaseModel):
    message: str
    context_limit: int = 10
    # Optional per-request LLM overrides (from frontend settings)
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None


class ChatResponse(BaseModel):
    response: str
    sources: list[dict]


def _build_provider_from_request(req: ChatRequest):
    """Build a one-off LLM provider using request-level overrides."""
    provider_name = (req.llm_provider or os.environ.get("LLM_PROVIDER", "anthropic")).lower()

    if provider_name == "anthropic":
        import anthropic as sdk
        key = req.llm_api_key or os.environ.get("LLM_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        model = req.llm_model or os.environ.get("LLM_MODEL", "claude-sonnet-4-6")

        class _P(AnthropicProvider):
            def __init__(self):
                self._client = sdk.Anthropic(api_key=key)
                self._model = model
        return _P()

    elif provider_name == "openai":
        from openai import OpenAI
        key = req.llm_api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        model = req.llm_model or os.environ.get("LLM_MODEL", "gpt-4o")
        base_url = req.llm_base_url or os.environ.get("LLM_BASE_URL") or None

        class _P(OpenAIProvider):
            def __init__(self):
                self._client = OpenAI(api_key=key, base_url=base_url)
                self._model = model
        return _P()

    elif provider_name == "ollama":
        import httpx
        base_url = req.llm_base_url or os.environ.get("LLM_BASE_URL", "http://localhost:11434")
        model = req.llm_model or os.environ.get("LLM_MODEL", "llama3.2")

        class _P(OllamaProvider):
            def __init__(self):
                self._client = httpx.Client(timeout=120.0)
                self._url = f"{base_url.rstrip('/')}/api/chat"
                self._model = model
        return _P()

    elif provider_name == "gemini":
        import google.generativeai as genai
        key = req.llm_api_key or os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY")
        model = req.llm_model or os.environ.get("LLM_MODEL", "gemini-2.0-flash")

        class _P(GeminiProvider):
            def __init__(self):
                self._model_name = model
                self._api_key = key
        return _P()

    elif provider_name == "openrouter":
        key = req.llm_api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        model = req.llm_model or None  # None = use fallback chain
        return OpenRouterProvider(api_key=key, model=model)

    raise ValueError(f"Unknown provider: {provider_name!r}")


def retrieve_context(query: str, limit: int = 10) -> list[dict]:
    """Retrieve relevant chunks via semantic search."""
    embedding = embed_text(query)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.text, t.title, t.series,
                       1 - (c.embedding <=> %s::vector) as similarity
                FROM chunks c
                JOIN transcripts t ON t.id = c.transcript_id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
            """, (str(embedding), str(embedding), limit))
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {"text": row[0], "title": row[1], "series": row[2], "similarity": round(float(row[3]), 4)}
        for row in rows
    ]


@router.post("/chat", response_model=ChatResponse)
def chat_with_watts(req: ChatRequest):
    """Chat with an AI embodying Alan Watts, grounded in his actual words."""
    sources = retrieve_context(req.message, limit=req.context_limit)

    context_parts = []
    for i, src in enumerate(sources, 1):
        label = src["title"]
        if src["series"]:
            label = f"{src['series']} - {src['title']}"
        context_parts.append(f"[Excerpt {i} from \"{label}\"]\n{src['text']}")

    context_block = "\n\n---\n\n".join(context_parts)

    user_message = f"""Based on these excerpts from your lectures and writings, please respond to the following question or topic.

TRANSCRIPT EXCERPTS:
{context_block}

QUESTION/TOPIC: {req.message}"""

    # Use per-request provider if any override provided, else singleton
    try:
        if any([req.llm_provider, req.llm_model, req.llm_api_key, req.llm_base_url]):
            provider = _build_provider_from_request(req)
        else:
            provider = get_provider()

        response_text = provider.generate(
            system=ALAN_WATTS_SYSTEM_PROMPT,
            user=user_message,
            max_tokens=1500,
        )
    except Exception as e:
        err = str(e)
        if "credit balance" in err or "billing" in err.lower():
            raise HTTPException(status_code=402, detail="LLM API credit balance too low. Please configure a valid API key in Settings.")
        elif "api_key" in err.lower() or "authentication" in err.lower() or "401" in err:
            raise HTTPException(status_code=401, detail="Invalid or missing API key. Please check your settings.")
        else:
            raise HTTPException(status_code=503, detail=f"LLM error: {err}")

    return ChatResponse(
        response=response_text,
        sources=[{"title": s["title"], "series": s["series"], "similarity": s["similarity"]}
                 for s in sources[:5]]
    )
