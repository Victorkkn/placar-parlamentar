from django.apps import AppConfig


class ApiConfig(AppConfig):
    name = "placar.api"
    label = "api"
    verbose_name = "Public read-only API"
