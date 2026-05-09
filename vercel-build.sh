#!/usr/bin/env bash
set -euo pipefail

echo "Starting Vercel build script: running Django migrations and collectstatic"

# Run migrations (idempotent)
python manage.py migrate --noinput

# Collect static files (ignore if not configured)
python manage.py collectstatic --noinput || true

echo "Build script completed."