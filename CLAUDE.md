# Alan Watts Library

> 238 transcripts, 1.7M words, 4,293 vectorized chunks — the complete indexed mind of Alan Watts.

## You Are

A **data scientist and Alan Watts domain expert** working with a fully vectorized corpus of his lectures, essays, and dialogues. Understand both the technical pipeline (embeddings, clustering, RAG) and the philosophical content.

### Key Themes (Philosophy Context)

- **The self is a hoax**: Ego ("skin-encapsulated ego") is social fiction — you are the universe experiencing itself
- **Wu wei**: Action through non-action; flow with reality like water, not against it
- **Lila** (life as play): Existence is a game, not a problem to solve
- **The eternal now**: Past/future are abstractions; only the present is real
- **Mutual arising**: All opposites (self/other, life/death) are aspects of one process
- **Style**: Warm, witty, conversational — "sharing a wonderful secret" — never preachy

## Quick Start

```bash
source ~/.secrets/hercules.env    # REQUIRED before any docker/db commands

make run                          # Start all 3 services (db + api + frontend)
make dev                          # Local API hot-reload on port 8131
make run-pipeline                 # Full ingestion: load → chunk → embed → cluster
make mcp                          # Start MCP server (stdio)
make logs                         # Tail API logs
make stop                         # Stop all containers
```

## API (port 8131)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| GET | `/api/search?q=...&limit=10` | Semantic search (pgvector cosine) |
| POST | `/api/chat` | RAG chat — AI Alan Watts Librarian persona |
| GET | `/api/transcripts` | Browse (filter: `series=`, `search=`) |
| GET | `/api/transcripts/{id}` | Full transcript text |
| GET | `/api/series` | Lecture series list |
| GET | `/api/topics` | 15 auto-discovered topics |
| GET | `/api/topics/{id}` | Topic detail + associated transcripts |
| GET/POST | `/api/settings` | LLM provider config + test connection |

```json
POST /api/chat  →  {"message": "What is wu wei?", "context_limit": 10}
```

## Architecture

```
Query → Embed (all-mpnet-base-v2, 768d, local)
  → pgvector HNSW cosine search → Top-k chunks + parent transcripts
  → RAG prompt → LLM (pluggable: anthropic|openai|ollama|gemini|openrouter)
  → Response grounded in actual lectures
```

## MCP Server

7 tools exposed to Claude Code: `search` `chat` `list_transcripts` `get_transcript` `list_series` `list_topics` `get_topic`

```bash
make mcp    # stdio MCP server — update mcp.json cwd+env first
```

## Project Structure

```
config/
├── settings.py          # DATABASE_URL, EMBEDDING_MODEL, CHUNK_SIZE_TOKENS
└── init.sql             # Schema: sources, transcripts, chunks, topics
src/
├── api/main.py          # FastAPI app + CORS
├── api/routes/          # search.py | chat.py | browse.py | settings.py
├── embeddings/provider.py  # Singleton SentenceTransformer (all-mpnet-base-v2)
├── ingestion/           # loader.py | chunker.py | embed.py | cluster.py
├── llm/provider.py      # Abstract LLM + Anthropic|OpenAI|Ollama|Gemini|OpenRouter
├── scraper/             # deoxy.py | youtube.py | archive_org.py | pipeline.py
└── mcp_server.py        # FastMCP server (7 tools)
frontend/
├── app/                 # page.tsx | chat/ | browse/ | topics/ | settings/
├── components/          # Nav | SearchBar | ChatInterface | TranscriptViewer | ...
└── lib/api.ts           # All API calls centralized here — edit this for new endpoints
data/
├── github-can-sahin/    # 110 transcripts (JSON — gitignored)
└── github-chaosinside/  # 121 transcripts (txt by series — gitignored)
scripts/
├── export-db.sh         # pg_dump → .sql.gz
└── restore-db.sh        # Restore from file or URL
tests/                   # Pytest suite — add tests here
```

## Database

```
PostgreSQL 16 + pgvector @ 127.0.0.1:5441

transcripts  → 238 rows  (full_text, title, series, content_hash for dedup)
chunks       → 4,293 rows (text, embedding vector(768), HNSW index)
topics       → 15 rows   (name, JSON description with keywords/chunk_count)
transcript_topics → relevance scores
```

```bash
docker compose exec db psql -U alan_watts alan_watts   # Connect

-- Useful queries
SELECT title, series FROM transcripts WHERE full_text ILIKE '%wu wei%';
SELECT name, (description::json->>'chunk_count')::int FROM topics ORDER BY 2 DESC;
```

## Extension Patterns

### Add an API Route
1. Create `src/api/routes/myroute.py` — follow `browse.py` pattern
2. Register in `src/api/main.py`: `app.include_router(myroute.router, prefix="/api")`
3. Add types + fetch call in `frontend/lib/api.ts`

### Add a Frontend Page
1. Create `frontend/app/mypage/page.tsx` (Next.js App Router)
2. Add nav link in `frontend/components/Nav.tsx`
3. Design system: use `var(--bg)` `var(--accent)` `.card` `.btn` `.badge` CSS classes

### Add a Scraper
1. Create `src/scraper/myscraper.py` returning transcript dicts
2. Import + call in `src/scraper/pipeline.py`
3. Load via `loader.py` — SHA-256 dedup is automatic

### Add Transcripts / Tune RAG
```bash
make run-pipeline          # load → chunk → embed → cluster (full pipeline)
# NOTE: re-embedding 4,293 chunks is expensive — ask before running embed.py
```
- System prompt → `src/api/routes/chat.py:ALAN_WATTS_SYSTEM_PROMPT`
- Chunk size → `config/settings.py:CHUNK_SIZE_TOKENS` / `CHUNK_OVERLAP_TOKENS`
- Topic count → `src/ingestion/cluster.py:k=15`

## Testing

```bash
pytest tests/ -v                  # All tests
pytest tests/test_api.py -v       # API endpoint tests
pytest tests/ --cov=src           # With coverage report
```

## Environment

```bash
# Required
ALAN_WATTS_DB_PASSWORD=...

# LLM (anthropic | openai | ollama | gemini | openrouter)
LLM_PROVIDER=openrouter
LLM_MODEL=                        # leave blank → provider default
LLM_API_KEY=                      # not needed for ollama
LLM_BASE_URL=                     # ollama: http://localhost:11434
OPENROUTER_API_KEY=               # for openrouter

# Pipeline only (bulk embedding)
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

Copy `.env.example` → `.env` for local dev.

## Critical Rules

### MUST
- `source ~/.secrets/hercules.env` before docker/db commands
- Read files before editing
- DB binds to `127.0.0.1` only — never `0.0.0.0`
- SHA-256 dedup before embedding — `loader.py` handles this automatically
- Scraping: ≥1s delay between requests

### NEVER
- Expose database port to internet
- Hardcode API keys or passwords
- Re-embed entire corpus without explicit approval (4,293 chunks = expensive)
- Create docs files unless asked

## Deployment

```bash
source ~/.secrets/hercules.env
make run                          # All services

# Rebuild frontend with baked-in public URL
NEXT_PUBLIC_API_URL=https://alanwatts.herakles.dev docker compose up -d --build frontend

~/deploy.sh {status|health|restart|logs} alan-watts   # Hercules platform helper
```

**URLs**: `https://alanwatts.herakles.dev` | API: `127.0.0.1:8131` | DB: `127.0.0.1:5441` | Frontend: `127.0.0.1:3131`

---

## Fork Pattern

This library is a **forkable scaffold**. One command clones the full stack for any author/corpus.

### Fork a new library

```bash
./scripts/fork-library.sh \
  --name terence-mckenna \
  --title "Terence McKenna Library" \
  --author "Terence McKenna" \
  --domain "philosophy" \
  --subdomain "mckenna.herakles.dev"
```

Creates `/home/hercules/terence-mckenna/` as a fully independent stack.

### What the fork script does
1. Validates `--name` is a slug (lowercase + hyphens)
2. Auto-assigns 3 ports from PORT_REGISTRY (db, api, frontend)
3. `rsync` copies this stack (excludes `.git`, `data/`, `node_modules`, `.env`)
4. Writes `config/library.yml` filled with provided args + TODO sections
5. Updates `docker-compose.yml` (container names, ports, DB credentials)
6. Updates `Makefile` (container references, port)
7. Replaces `src/ingestion/loader.py` with a stub for the user to implement
8. Clears `data/` → `data/README.md`
9. Updates `mcp.json` (cwd + server name)
10. Registers ports in `~/system-apps-config/PORT_REGISTRY.json`
11. Creates `spec.md` from template
12. `git init` in new directory

### library.yml — single source of identity

Everything author-specific lives in `config/library.yml`:

| Section | Controls |
|---------|---------|
| `library` | Name, title, author, subdomain, description |
| `ports` | DB / API / frontend ports |
| `ragPersona` | AI persona: name, voice, key themes, system prompt template |
| `topicRules` | K-Means cluster labeling rules (triggers → topic label) |
| `frontend` | Search suggestions, hero tagline, accent color |

### After forking — next steps

```bash
cd /home/hercules/NEW-LIBRARY
# 1. Edit config/library.yml — fill all TODO sections
# 2. Add corpus data to data/
# 3. Implement src/ingestion/loader.py
# 4. export NEW_LIBRARY_DB_PASSWORD=...
# 5. make run
# 6. make run-pipeline
```

### Templates

| File | Purpose |
|------|---------|
| `scripts/templates/library.yml.template` | Blank library config template |
| `scripts/templates/loader-stub.py` | Data loader skeleton |
| `scripts/templates/spec.md.template` | V11 spec for new library |

### Architecture (library.yml → code)

```
config/library.yml
  ↓ config/library_config.py (PyYAML → typed dataclasses)
  ↓ config/settings.py (LIB = get_library_config())
  ├─ src/api/routes/chat.py   → LIB.rag_persona.build_system_prompt()
  ├─ src/api/routes/info.py   → LIB.library + LIB.frontend + live DB counts
  └─ src/ingestion/cluster.py → LIB.topic_rules
```

Frontend fetches `/api/info` on mount → Nav shows live corpus counts, page shows dynamic suggestions.

---

**Port**: 8131 | **Status**: active | **Last updated**: 2026-02-27
