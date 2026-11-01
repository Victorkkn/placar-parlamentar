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
echo "== tests"
uv run pytest -q
echo "== dependency audit"
uv run pip-audit --progress-spinner off
cd "$root"
echo "== secrets (commits on this branch not yet in main)"
if git rev-parse --verify -q main >/dev/null && [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
  gitleaks git --redact --no-banner --log-opts="main..HEAD" .
else
  gitleaks git --redact --no-banner .
fi
echo "== all checks passed"
