from django.apps import AppConfig


class ApisConfig(AppConfig):
    name = 'apis'

    def ready(self):
        import apis.signals
