#!/bin/sh
# Full checks before merging into main (decision 0016). Needs Docker running for PostgreSQL.
set -e
root=$(git rev-parse --show-toplevel)
cd "$root"
echo "== database"
docker compose exec -T db pg_isready -q || { echo "PostgreSQL is not running: docker compose up -d db" >&2; exit 1; }
cd backend
echo "== lint"
uv run ruff check .
uv run ruff format --check .
echo "== migrations"
uv run python manage.py makemigrations --check --dry-run
echo "== tests and coverage"
uv run coverage run -m pytest -q
uv run coverage report --include="placar/metrics/*" --fail-under=90
echo "== dependency audit"
uv run pip-audit --progress-spinner off
cd "$root"
if [ -f frontend/package.json ]; then
  echo "== frontend"
  (cd frontend && npm run -s lint && npm run -s typecheck && mkdir -p node_modules/.cache && npm run -s check:api >/dev/null \
    && npm test --silent && npm run -s build >/dev/null \
    && npm audit --omit=dev --audit-level=moderate)
fi
echo "== secrets (commits on this branch not yet in main)"
if git rev-parse --verify -q main >/dev/null && [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
  gitleaks git --redact --no-banner --log-opts="main..HEAD" .
else
  gitleaks git --redact --no-banner .
fi
echo "== all checks passed"
