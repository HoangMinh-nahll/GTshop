from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Kích hoạt signals giữ giỏ hàng
        import accounts.signals  # noqa