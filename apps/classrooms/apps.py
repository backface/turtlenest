from django.apps import AppConfig


class ClassroomsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.classrooms"
    label = "classrooms"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        pass

        # from apps.classrooms import signals
