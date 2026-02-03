#!/bin/bash
# =============================================================
# scripts/reset_db.sh
# Wipes the TimescaleDB volume so the schema is recreated fresh
# on the next `docker compose up`.
# Run from the PROJECT ROOT directory.
# =============================================================

set -e

echo "=== Maritime Observability – Database Reset ==="
echo ""
echo "This will DELETE all data stored in TimescaleDB."
read -rp "Are you sure? (y/N): " confirm

[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

echo ""
echo "→ Stopping all services …"
docker compose down

echo "→ Removing database volume …"
# docker compose down -v removes ALL volumes; we only need to drop the DB one.
# The volume name follows the pattern: <project-dir>_timescaledb_data
# Using -v with down is the simplest cross-platform approach:
docker compose down -v

echo ""
echo "Done.  Run  docker compose up --build  to restart with a fresh database."
