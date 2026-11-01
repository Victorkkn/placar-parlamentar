#!/usr/bin/env python3
"""Record test fixtures from the raw API cache (decision 0011). Run by the project owner.

Usage (from the repo root):
    python3 scripts/record_fixtures.py            # use cached responses only
    python3 scripts/record_fixtures.py --fetch    # also download missing cases (live requests)

This wrapper runs the backend's `record_fixtures` management command with uv.
"""

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"

if __name__ == "__main__":
    command = ["uv", "run", "python", "manage.py", "record_fixtures", *sys.argv[1:]]
    sys.exit(subprocess.call(command, cwd=BACKEND))  # noqa: S603 - fixed command, no shell
