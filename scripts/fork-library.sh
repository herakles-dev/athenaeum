#!/usr/bin/env bash
# fork-library.sh — Clone the alan-watts RAG stack to a new library.
#
# Usage:
#   ./scripts/fork-library.sh \
#     --name terence-mckenna \
#     --title "Terence McKenna Library" \
#     --author "Terence McKenna" \
#     --domain "philosophy" \
#     --subdomain "mckenna.herakles.dev"
#
# What it does:
#   1. Validates name is a valid slug (lowercase + hyphens)
#   2. Auto-assigns 3 ports (db, api, frontend) not in use
#   3. rsyncs alan-watts/ → /home/hercules/$NAME/ (clean copy)
#   4. Writes config/library.yml from template + provided args
#   5. Updates docker-compose.yml (container names, ports, db creds)
#   6. Updates Makefile (container references)
#   7. Replaces src/ingestion/loader.py with stub
#   8. Clears data/ → data/README.md
#   9. Updates mcp.json (cwd + server name)
#  10. Registers in PORT_REGISTRY.json
#  11. Creates spec.md from template
#  12. git init in new directory
#  13. Prints next steps

set -euo pipefail

ALAN_WATTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT_REGISTRY="${HOME}/system-apps-config/PORT_REGISTRY.json"
HERCULES_DIR="${HOME}"

# ── Argument parsing ──────────────────────────────────────────────────────────

NAME=""
TITLE=""
AUTHOR=""
DOMAIN="philosophy"
SUBDOMAIN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)      NAME="$2";      shift 2 ;;
    --title)     TITLE="$2";     shift 2 ;;
    --author)    AUTHOR="$2";    shift 2 ;;
    --domain)    DOMAIN="$2";    shift 2 ;;
    --subdomain) SUBDOMAIN="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Validation ────────────────────────────────────────────────────────────────

die() { echo "ERROR: $*" >&2; exit 1; }

[[ -n "$NAME" ]]   || die "--name is required"
[[ -n "$TITLE" ]]  || die "--title is required"
[[ -n "$AUTHOR" ]] || die "--author is required"

if ! [[ "$NAME" =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$ ]]; then
  die "--name must be a lowercase slug (letters, digits, hyphens). Got: '$NAME'"
fi

DEST="${HERCULES_DIR}/${NAME}"
if [[ -d "$DEST" ]]; then
  die "Directory already exists: $DEST — choose a different name or remove it first."
fi

[[ -z "$SUBDOMAIN" ]] && SUBDOMAIN="${NAME}.herakles.dev"

# Derive underscore and UPPER variants
NAME_UNDERSCORE="${NAME//-/_}"
NAME_UPPER="${NAME_UNDERSCORE^^}"

echo "=== Forking alan-watts → ${NAME} ==="
echo "    Title:     $TITLE"
echo "    Author:    $AUTHOR"
echo "    Domain:    $DOMAIN"
echo "    Subdomain: $SUBDOMAIN"
echo "    Dest:      $DEST"
echo ""

# ── Port assignment ───────────────────────────────────────────────────────────

# Collect all in-use ports from PORT_REGISTRY and live netstat
get_used_ports() {
  local registry_ports=""
  if [[ -f "$PORT_REGISTRY" ]]; then
    # Extract all numeric port keys from the JSON
    registry_ports=$(python3 -c "
import json, sys
with open('$PORT_REGISTRY') as f:
    data = json.load(f)

ports = set()
def extract_ports(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            try:
                p = int(k)
                if 1024 < p < 65536:
                    ports.add(p)
            except ValueError:
                pass
            extract_ports(v)
    elif isinstance(obj, list):
        for item in obj:
            extract_ports(item)

extract_ports(data)
print(' '.join(str(p) for p in sorted(ports)))
" 2>/dev/null || echo "")
  fi

  local live_ports=""
  if command -v ss &>/dev/null; then
    live_ports=$(ss -tlnp 2>/dev/null | awk 'NR>1{split($4,a,":"); p=a[length(a)]; if (p+0>1024) print p+0}' | sort -u | tr '\n' ' ')
  elif command -v netstat &>/dev/null; then
    live_ports=$(netstat -tlnp 2>/dev/null | awk '{split($4,a,":"); p=a[length(a)]; if (p+0>1024) print p+0}' | sort -u | tr '\n' ' ')
  fi

  echo "$registry_ports $live_ports"
}

assign_ports() {
  local used
  used=$(get_used_ports)

  # Find 3 available ports: one in 5440-5499 range (db), two in 8140-8199 range (api+frontend)
  local db_port="" api_port="" fe_port=""

  for p in $(seq 5442 5499); do
    if ! echo "$used" | grep -qw "$p"; then
      db_port=$p
      break
    fi
  done

  for p in $(seq 8140 8199); do
    if ! echo "$used" | grep -qw "$p"; then
      api_port=$p
      break
    fi
  done

  for p in $(seq 3140 3199); do
    if ! echo "$used" | grep -qw "$p"; then
      fe_port=$p
      break
    fi
  done

  [[ -n "$db_port" ]]  || die "No free DB port found in 5442-5499 range"
  [[ -n "$api_port" ]] || die "No free API port found in 8140-8199 range"
  [[ -n "$fe_port" ]]  || die "No free frontend port found in 3140-3199 range"

  echo "$db_port $api_port $fe_port"
}

read -r DB_PORT API_PORT FE_PORT < <(assign_ports)
echo "    Ports:     db=$DB_PORT  api=$API_PORT  frontend=$FE_PORT"
echo ""

# ── rsync ─────────────────────────────────────────────────────────────────────

echo "→ Copying files..."
rsync -a --exclude='.git' \
         --exclude='data/github-*' \
         --exclude='data/*.sql.gz' \
         --exclude='__pycache__' \
         --exclude='*.pyc' \
         --exclude='.env' \
         --exclude='node_modules' \
         --exclude='.next' \
         --exclude='frontend/.next' \
         "${ALAN_WATTS_DIR}/" "${DEST}/"

# ── library.yml ───────────────────────────────────────────────────────────────

echo "→ Writing config/library.yml..."
cat > "${DEST}/config/library.yml" << EOF
library:
  name: ${NAME}
  title: ${TITLE}
  author: ${AUTHOR}
  domain: ${DOMAIN}
  subdomain: ${SUBDOMAIN}
  description: "TODO: Add corpus description (e.g. 100 transcripts, 500K words...)"

ports:
  db: ${DB_PORT}
  api: ${API_PORT}
  frontend: ${FE_PORT}

ragPersona:
  name: ${AUTHOR}
  shortDescription: "TODO: Brief description of ${AUTHOR}'s background and work"
  voice: "TODO: Describe the voice/tone (e.g. 'warmth, humor, visionary insight')"
  keyThemes:
    - "TODO: Key theme 1"
    - "TODO: Key theme 2"
    - "TODO: Key theme 3"
  systemPromptTemplate: |
    You are {name}, {short_description}.

    You speak with {voice}.

    Key aspects of your philosophical/intellectual voice:
    {key_themes_bullet}

    CRITICAL RULES:
    1. ONLY use information from the provided transcript excerpts to answer questions
    2. If the excerpts don't contain relevant information, say so honestly — don't fabricate
    3. Weave the actual words and phrases from the excerpts into your response
    4. Cite which lecture/talk the ideas come from when possible
    5. Stay in character but never claim to have experiences you (as an AI) haven't had
    6. When quoting directly, use the actual words from the transcripts

topicRules:
  # TODO: Add topic rules for ${AUTHOR}'s corpus.
  # Each rule: triggers (list of keywords/phrases), label, weight (1-3).
  # Higher weight = rule scores higher when its triggers match cluster keywords.
  # Example:
  # - triggers: [consciousness, psychedelic, mushroom, dmt]
  #   label: "Psychedelics & Consciousness"
  #   weight: 3
  - triggers: [TODO_keyword_1, TODO_keyword_2]
    label: "TODO Topic Label"
    weight: 2

frontend:
  suggestions:
    - "TODO: suggestion 1"
    - "TODO: suggestion 2"
    - "TODO: suggestion 3"
    - "TODO: suggestion 4"
  heroTagline: "TODO: Explore the complete lectures, essays & dialogues"
  accentColor: "#d97706"
EOF

# ── docker-compose.yml ────────────────────────────────────────────────────────

echo "→ Updating docker-compose.yml..."
sed -i \
  -e "s/alan_watts_db/${NAME_UNDERSCORE}_db/g" \
  -e "s/alan_watts_api/${NAME_UNDERSCORE}_api/g" \
  -e "s/alan_watts_frontend/${NAME_UNDERSCORE}_frontend/g" \
  -e "s/alan_watts_pgdata/${NAME_UNDERSCORE}_pgdata/g" \
  -e "s/ALAN_WATTS_DB_PASSWORD/${NAME_UPPER}_DB_PASSWORD/g" \
  -e "s/alan_watts:5432/${NAME_UNDERSCORE}:5432/g" \
  -e "s|127\.0\.0\.1:5441:5432|127.0.0.1:${DB_PORT}:5432|g" \
  -e "s|127\.0\.0\.1:8131:8000|127.0.0.1:${API_PORT}:8000|g" \
  -e "s|127\.0\.0\.1:3131:3000|127.0.0.1:${FE_PORT}:3000|g" \
  -e "s/postgresql:\/\/alan_watts:\${ALAN_WATTS_DB_PASSWORD}/postgresql:\/\/${NAME_UNDERSCORE}:\${${NAME_UPPER}_DB_PASSWORD}/g" \
  -e "s/POSTGRES_DB: alan_watts/POSTGRES_DB: ${NAME_UNDERSCORE}/g" \
  -e "s/POSTGRES_USER: alan_watts/POSTGRES_USER: ${NAME_UNDERSCORE}/g" \
  -e "s|@db:5432/alan_watts|@db:5432/${NAME_UNDERSCORE}|g" \
  "${DEST}/docker-compose.yml"

# ── Makefile ──────────────────────────────────────────────────────────────────

echo "→ Updating Makefile..."
sed -i \
  -e "s/alan_watts/${NAME_UNDERSCORE}/g" \
  -e "s/Alan Watts/${TITLE}/g" \
  -e "s/ALAN_WATTS/${NAME_UPPER}/g" \
  "${DEST}/Makefile"

# Update dev port in Makefile
sed -i "s/--port 8131/--port ${API_PORT}/g" "${DEST}/Makefile"

# ── mcp.json ──────────────────────────────────────────────────────────────────

echo "→ Updating mcp.json..."
cat > "${DEST}/mcp.json" << EOF
{
  "mcpServers": {
    "${NAME}": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "${DEST}",
      "env": {
        "${NAME_UPPER}_DB_PASSWORD": "\${${NAME_UPPER}_DB_PASSWORD}",
        "LLM_PROVIDER": "\${LLM_PROVIDER:-openrouter}",
        "LLM_MODEL": "\${LLM_MODEL:-}",
        "LLM_API_KEY": "\${LLM_API_KEY:-}",
        "OPENROUTER_API_KEY": "\${OPENROUTER_API_KEY:-}",
        "ANTHROPIC_API_KEY": "\${ANTHROPIC_API_KEY:-}"
      }
    }
  }
}
EOF

# ── settings.py DB URL ────────────────────────────────────────────────────────

echo "→ Updating config/settings.py DB connection string..."
sed -i \
  -e "s/alan_watts:\${os\.environ\.get('ALAN_WATTS_DB_PASSWORD', '')}@127\.0\.0\.1:5441\/alan_watts/${NAME_UNDERSCORE}:\${os.environ.get('${NAME_UPPER}_DB_PASSWORD', '')}@127.0.0.1:${DB_PORT}\/${NAME_UNDERSCORE}/g" \
  "${DEST}/config/settings.py"

# ── data/ cleanup ─────────────────────────────────────────────────────────────

echo "→ Setting up data/ directory..."
mkdir -p "${DEST}/data"
find "${DEST}/data" -mindepth 1 -maxdepth 1 -not -name 'README.md' -exec rm -rf {} + 2>/dev/null || true

cat > "${DEST}/data/README.md" << 'EOF'
# data/

Place your corpus data files here before running the ingestion pipeline.

## Expected formats

### JSON transcripts (github-style)
```
data/
  github-AUTHOR/
    transcript-1.json
    transcript-2.json
    ...
```

Each JSON file should contain:
```json
{
  "title": "Lecture Title",
  "series": "Series Name",
  "text": "Full transcript text...",
  "source_url": "https://...",
  "video_url": "https://..."
}
```

### Plain text transcripts
```
data/
  transcripts/
    SERIES_NAME/
      lecture-1.txt
      lecture-2.txt
```

## Ingestion pipeline

After placing data here, run:
```bash
make run-pipeline   # load → chunk → embed → cluster
```

Or step by step:
```bash
PYTHONPATH=. python3 -c "from src.ingestion.loader import run; run()"
PYTHONPATH=. python3 -c "from src.ingestion.chunker import run; run()"
PYTHONPATH=. python3 -c "from src.ingestion.embed import run; run()"
PYTHONPATH=. python3 -c "from src.ingestion.cluster import run; run()"
```

**Note**: Embedding is expensive. The loader uses SHA-256 dedup — running it multiple
times is safe, only new/changed content will be embedded.
EOF

# ── loader.py stub ────────────────────────────────────────────────────────────

echo "→ Replacing src/ingestion/loader.py with stub..."
cp "${ALAN_WATTS_DIR}/scripts/templates/loader-stub.py" \
   "${DEST}/src/ingestion/loader.py"

# ── PORT_REGISTRY.json ────────────────────────────────────────────────────────

if [[ -f "$PORT_REGISTRY" ]]; then
  echo "→ Registering ports in PORT_REGISTRY.json..."
  python3 - << PYEOF
import json, copy

registry_path = "${PORT_REGISTRY}"
with open(registry_path) as f:
    data = json.load(f)

# Add to development_apps (or create it)
if "development_apps" not in data.get("allocations", {}):
    data.setdefault("allocations", {})["development_apps"] = {}

data["allocations"]["development_apps"]["${DB_PORT}"] = {
    "service": "${NAME}-db",
    "container": "${NAME_UNDERSCORE}_db",
    "type": "database",
    "framework": "postgresql",
    "subdomain": "",
    "status": "pending",
    "notes": "Forked from alan-watts. DB for ${NAME}."
}
data["allocations"]["development_apps"]["${API_PORT}"] = {
    "service": "${NAME}-api",
    "container": "${NAME_UNDERSCORE}_api",
    "type": "api",
    "framework": "fastapi",
    "subdomain": "${SUBDOMAIN}",
    "status": "pending",
    "notes": "Forked from alan-watts. API for ${NAME}."
}
data["allocations"]["development_apps"]["${FE_PORT}"] = {
    "service": "${NAME}-frontend",
    "container": "${NAME_UNDERSCORE}_frontend",
    "type": "web",
    "framework": "nextjs",
    "subdomain": "${SUBDOMAIN}",
    "status": "pending",
    "notes": "Forked from alan-watts. Frontend for ${NAME}."
}

with open(registry_path, "w") as f:
    json.dump(data, f, indent=2)
print("  Registered ports ${DB_PORT}, ${API_PORT}, ${FE_PORT}")
PYEOF
fi

# ── spec.md ───────────────────────────────────────────────────────────────────

echo "→ Creating spec.md from template..."
sed \
  -e "s/{{NAME}}/${NAME}/g" \
  -e "s/{{TITLE}}/${TITLE}/g" \
  -e "s/{{AUTHOR}}/${AUTHOR}/g" \
  -e "s/{{DOMAIN}}/${DOMAIN}/g" \
  -e "s/{{SUBDOMAIN}}/${SUBDOMAIN}/g" \
  -e "s/{{DB_PORT}}/${DB_PORT}/g" \
  -e "s/{{API_PORT}}/${API_PORT}/g" \
  -e "s/{{FE_PORT}}/${FE_PORT}/g" \
  "${ALAN_WATTS_DIR}/scripts/templates/spec.md.template" \
  > "${DEST}/spec.md"

# ── git init ──────────────────────────────────────────────────────────────────

echo "→ Initializing git repository..."
git -C "${DEST}" init -q
git -C "${DEST}" add .
git -C "${DEST}" commit -q -m "Initial fork from alan-watts scaffold"

# ── Summary ───────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Library forked: ${TITLE}"
echo "  Location:       ${DEST}/"
echo "  Ports:          db=${DB_PORT}  api=${API_PORT}  frontend=${FE_PORT}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit config/library.yml — fill in all TODO sections"
echo "     cd ${DEST}"
echo "     \$EDITOR config/library.yml"
echo ""
echo "  2. Add your corpus data to data/"
echo "     (See data/README.md for expected formats)"
echo ""
echo "  3. Implement the data loader"
echo "     \$EDITOR src/ingestion/loader.py"
echo ""
echo "  4. Set the DB password in your environment"
echo "     export ${NAME_UPPER}_DB_PASSWORD=your_secure_password"
echo ""
echo "  5. Start the stack"
echo "     source ~/.secrets/hercules.env"
echo "     make run"
echo ""
echo "  6. Run the ingestion pipeline"
echo "     make run-pipeline"
echo ""
echo "  7. Open http://localhost:${FE_PORT}"
echo ""
