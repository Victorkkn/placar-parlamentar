"""Development settings: only on the owner's machine (decision 0013)."""

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
