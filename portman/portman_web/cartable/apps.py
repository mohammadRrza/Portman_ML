from django.apps import AppConfig


class CartableConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cartable'

    def ready(self):
        import cartable.signals