from django.apps import AppConfig


class OltConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'olt'

    def ready(self):
        import olt.signals
