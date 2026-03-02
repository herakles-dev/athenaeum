#!/bin/bash
# Restore the alan_watts corpus database from a gzipped SQL dump.
# Usage: ./scripts/restore-db.sh [dump-file-or-url]
#
# If no argument is given, checks for alan_watts_corpus.sql.gz locally.
# If a URL is given, downloads it first.

set -euo pipefail

SOURCE="${1:-alan_watts_corpus.sql.gz}"
DB_CONTAINER="${DB_CONTAINER:-alan_watts_db}"
DB_USER="${DB_USER:-alan_watts}"
DB_NAME="${DB_NAME:-alan_watts}"

# Download if it looks like a URL
if [[ "$SOURCE" == http* ]]; then
    TMPFILE="$(mktemp /tmp/alan_watts_XXXX.sql.gz)"
    echo "→ Downloading ${SOURCE}..."
    curl -fL --progress-bar -o "$TMPFILE" "$SOURCE"
    SOURCE="$TMPFILE"
    trap "rm -f $TMPFILE" EXIT
fi

if [[ ! -f "$SOURCE" ]]; then
    echo "✗ Dump file not found: ${SOURCE}"
    echo "  Provide a local .sql.gz file or a download URL as the first argument."
    exit 1
fi

echo "→ Restoring ${SOURCE} into ${DB_NAME}..."
gunzip -c "$SOURCE" | docker exec -i "$DB_CONTAINER" \
    psql -U "$DB_USER" "$DB_NAME"

echo "✓ Restore complete."
