#!/usr/bin/env python3
"""Compare live official API responses with the recorded fixtures (decision 0011, item 20).

Run by hand from the repo root: python3 scripts/check_upstream.py
Makes one live request per fixture. Record any differences in docs/data-issues.md.
"""

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"

if __name__ == "__main__":
    command = ["uv", "run", "python", "manage.py", "check_upstream", *sys.argv[1:]]
    sys.exit(subprocess.call(command, cwd=BACKEND))  # noqa: S603 - fixed command, no shell
