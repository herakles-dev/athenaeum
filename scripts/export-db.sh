#!/bin/bash
# Export the fully-embedded alan_watts database to a gzipped SQL dump.
# Usage: ./scripts/export-db.sh [output-file]
# Output: alan_watts_corpus.sql.gz (default)

set -euo pipefail

OUTPUT="${1:-alan_watts_corpus.sql.gz}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5441}"
DB_USER="${DB_USER:-alan_watts}"
DB_NAME="${DB_NAME:-alan_watts}"

echo "→ Exporting database ${DB_NAME} to ${OUTPUT}..."
PGPASSWORD="${ALAN_WATTS_DB_PASSWORD}" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" \
    | gzip -9 > "$OUTPUT"

SIZE=$(du -sh "$OUTPUT" | cut -f1)
echo "✓ Export complete: ${OUTPUT} (${SIZE})"
