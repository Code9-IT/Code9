#!/bin/bash
# =============================================================
# scripts/reset_db.sh
# Wipes the TimescaleDB volume so the schema is recreated fresh
# on the next `docker compose up`.
# Run from the PROJECT ROOT directory.
#
# Only removes the database volume – the Ollama model cache
# (ollama_data) is preserved so you don't need to re-download
# llama3.2 (~2 GB) after a reset.
# =============================================================

set -e

echo "=== Maritime Observability – Database Reset ==="
echo ""
echo "This will DELETE all data stored in TimescaleDB."
echo "The Ollama model cache (ollama_data) is NOT affected."
read -rp "Are you sure? (y/N): " confirm

[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

echo ""
echo "→ Stopping all services …"
docker compose down

echo "→ Removing database volume (preserving Ollama cache) …"
# Docker Compose names volumes as: <project>_<volume-name>.
# The project name is derived from the directory name: lowercased,
# non-alphanumeric chars (except _ and -) stripped – same logic Compose uses.
PROJECT=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]_-')
VOLUME="${PROJECT}_timescaledb_data"

if docker volume inspect "$VOLUME" &>/dev/null; then
    docker volume rm "$VOLUME"
    echo "→ Removed volume: $VOLUME"
else
    echo "→ Volume '$VOLUME' not found (already removed or never created)."
fi

echo ""
echo "Done.  Run  docker compose up --build  to restart with a fresh database."
