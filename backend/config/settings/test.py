"""Test settings. Tests run offline (decision 0011)."""

import os

# Not a secret: used only by the test suite.
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-not-a-secret")

from .base import *  # noqa: E402, F403
from .base import PLACAR  # noqa: E402

DEBUG = False
ALLOWED_HOSTS = ["testserver"]
PLACAR = {**PLACAR, "RAW_CACHE_DIR": None}  # tests always pass their own temporary cache folder
