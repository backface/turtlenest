from django.apps import AppConfig


class LegacydbConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.legacydb"
    label = "legacydb"
