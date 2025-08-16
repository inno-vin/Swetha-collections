from django.apps import AppConfig

class StoreConfig(AppConfig):
    name = 'store'

    def ready(self):
        print("📦 store.signals loaded!")
        import store.signals