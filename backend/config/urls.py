"""URL routes: the read-only public API under /api/ (Phase C1)."""

from django.urls import path

from placar.api.api import api

urlpatterns = [
    path("api/", api.urls),
]
