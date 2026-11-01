"""Settings shared by every environment. Values come from environment variables (decision 0013).

The repo-root `.env` file is read if present; variables already set in the environment win.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


def _load_dotenv(path: Path) -> None:
    """Minimal `.env` reader: KEY=VALUE lines, `#` comments, optional quotes. Never overrides."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


_load_dotenv(REPO_ROOT / ".env")


def env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY is not set. Copy .env.example to .env and fill it in (decision 0012)."
    )

DEBUG = False
ALLOWED_HOSTS: list[str] = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "placar.legislators",
    "placar.sources",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME", "placar"),
        "USER": env("DATABASE_USER", "placar"),
        "PASSWORD": env("DATABASE_PASSWORD", ""),
        "HOST": env("DATABASE_HOST", "127.0.0.1"),
        "PORT": env("DATABASE_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Response headers (decision 0012).
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
X_FRAME_OPTIONS = "DENY"

# Project settings.
PLACAR = {
    # Raw API response cache (decision 0006).
    "RAW_CACHE_DIR": Path(env("PLACAR_RAW_CACHE_DIR", str(REPO_ROOT / "data" / "raw"))),
    "CACHE_TTL_HOURS": int(env("PLACAR_CACHE_TTL_HOURS", "24")),
    # Polite use of official APIs (decision 0012): at most 2 requests per second per API.
    "REQUESTS_PER_SECOND": min(float(env("PLACAR_REQUESTS_PER_SECOND", "2")), 2.0),
    "USER_AGENT": (
        "PlacarParlamentar/0.1 (projeto pessoal de transparencia; dados abertos oficiais)"
    ),
}

# Logs never contain visitor IPs, user agents, cookies or headers (decision 0012).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "loggers": {
        "placar": {"handlers": ["console"], "level": "INFO"},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
