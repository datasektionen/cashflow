from django.contrib.auth.models import User
from django.db import models


class ServiceAccount(models.Model):
    """Credentials for the service account interacting with the Fortnox API.

    We only allow one instance since we are only using a service account to perform all actions.
    This account should be authenticated by Kassör to allow Cashflow to interact with Fortnox.
    """

    authenticated_by = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    access_token = models.TextField(null=False)
    refresh_token = models.TextField(null=False)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.pk is None and ServiceAccount.objects.count() >= 1:
            raise ValueError("Only one service account is allowed.")
        super().save(*args, **kwargs)
