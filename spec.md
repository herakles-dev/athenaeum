# Project: Handbook Library (RAG Library)

## Intent

Build a semantic search + RAG chat library for Document Library's corpus.
Forked from the alan-watts RAG scaffold — a proven stack of FastAPI,
pgvector, and Next.js, now configured for Document Library's content.

**Goal**: Index Document Library's lectures/essays/writings and build a chat interface
where users can talk to an AI embodying Document Library, grounded in actual transcript excerpts.

## Stack

- Backend: FastAPI (Python 3.11) @ port 8140
- Database: PostgreSQL 16 + pgvector @ port 5442
- Embeddings: all-mpnet-base-v2 (local, 768d)
- Frontend: Next.js 14 (TypeScript + Tailwind) @ port 3140
- Config: config/library.yml (single source of identity)
- LLM: Pluggable (Anthropic | OpenAI | Ollama | Gemini | OpenRouter)
- Fork: Scaffolded from alan-watts via scripts/fork-library.sh

## Constraints

- Zero breaking changes to scaffold behavior
- DB binds to 127.0.0.1 only — never 0.0.0.0
- Re-embedding is expensive — never auto-trigger embed.py
- Secrets in ~/.secrets/hercules.env, never committed to git
- NEXT_PUBLIC_API_URL must be baked in at Docker build time

## Architecture

```
Query → Embed (all-mpnet-base-v2, 768d, local)
  → pgvector HNSW cosine search → Top-k chunks + parent transcripts
  → RAG prompt (built from config/library.yml ragPersona)
  → LLM (pluggable)
  → Response grounded in actual transcripts
```

Library identity: `config/library.yml` → `config/library_config.py` → `config/settings.py` → all modules

## Tasks

### Phase 1: Configure (complete library.yml first!)
- [ ] Edit `config/library.yml` — fill ALL TODO sections
  - [ ] Library metadata (name, title, author, description)
  - [ ] RAG persona (shortDescription, voice, keyThemes, systemPromptTemplate)
  - [ ] Topic rules (20-30 rules for knowledge-management corpus)
  - [ ] Frontend config (suggestions, heroTagline)
- [ ] Verify DB password env var: `export {{NAME_UPPER}}_DB_PASSWORD=...`

### Phase 2: Data Ingestion
- [ ] Source corpus data for Document Library
  - Where to get data: (TODO — list sources here)
  - Place in `data/` directory (see data/README.md)
- [ ] Implement `src/ingestion/loader.py`
  - Fill in `load_my_source()` function
  - Handle your specific data format (JSON / TXT / HTML / ...)
- [ ] Run ingestion: `make run-pipeline`
  - `load` → `chunk` → `embed` → `cluster`
  - Verify: `docker compose exec db psql -U {{NAME_UNDERSCORE}} {{NAME_UNDERSCORE}}`
    → `SELECT COUNT(*) FROM transcripts;`
    → `SELECT COUNT(*) FROM chunks;`

### Phase 3: Stack Validation
- [ ] Start stack: `make run`
- [ ] Test API: `curl http://localhost:8140/api/info`
- [ ] Test search: `curl "http://localhost:8140/api/search?q=test&limit=5"`
- [ ] Test chat: `curl -X POST http://localhost:8140/api/chat -d '{"message":"test"}' -H 'Content-Type:application/json'`
- [ ] Open frontend: http://localhost:3140
- [ ] Verify search suggestions match library.yml
- [ ] Verify Nav shows live corpus counts

### Phase 4: Tune & Deploy (optional)
- [ ] Tune system prompt in `config/library.yml` → `ragPersona.systemPromptTemplate`
- [ ] Tune topic rules to get better cluster labels → re-run `cluster.py`
- [ ] Configure LLM provider via `/settings` page
- [ ] Set up nginx + SSL for `library.herakles.dev`
- [ ] Build frontend with public URL:
      `NEXT_PUBLIC_API_URL=https://library.herakles.dev docker compose up -d --build frontend`

## Protocol

V11

## Notes

- This library was forked from `/home/hercules/alan-watts` on $(date +%Y-%m-%d)
- Reference implementation: https://alanwatts.herakles.dev
- Fork script: `/home/hercules/alan-watts/scripts/fork-library.sh`
- If stuck: read `/home/hercules/alan-watts/CLAUDE.md` for architecture patterns
