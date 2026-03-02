.PHONY: setup restore-db run stop run-pipeline mcp dev logs help

# Load .env if present
ifneq (,$(wildcard .env))
  include .env
  export
endif

help:
	@echo "Handbook Library Library — available targets:"
	@echo ""
	@echo "  setup          Start DB, restore corpus, start API"
	@echo "  restore-db     Download and restore the corpus database"
	@echo "  run            docker compose up -d (all services)"
	@echo "  stop           docker compose down"
	@echo "  run-pipeline   Run full ingestion: load → chunk → embed → cluster"
	@echo "  mcp            Start MCP server (stdio)"
	@echo "  dev            Run API with hot reload (local dev)"
	@echo "  logs           Tail API logs"

setup: restore-db run

restore-db:
	@echo "→ Starting database..."
	docker compose up -d db
	@echo "→ Waiting for database to be healthy..."
	@until docker compose exec db pg_isready -U handbook_library 2>/dev/null; do sleep 1; done
	@echo "→ Restoring corpus..."
	./scripts/restore-db.sh

run:
	docker compose up -d

stop:
	docker compose down

run-pipeline:
	PYTHONPATH=. python3 -c "from src.ingestion.loader import run; run()"
	PYTHONPATH=. python3 -c "from src.ingestion.chunker import run; run()"
	PYTHONPATH=. python3 -c "from src.ingestion.embed import run; run()"
	PYTHONPATH=. python3 -c "from src.ingestion.cluster import run; run()"

mcp:
	PYTHONPATH=. python3 -m src.mcp_server

dev:
	PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port 8140 --reload

logs:
	docker compose logs -f api
