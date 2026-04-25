from django.contrib.auth.models import User
from django.db import models


class APIUser(models.Model):
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
        if APIUser.objects.count() >= 1:
            raise ValueError("Only one API user is allowed.")
        super().save(*args, **kwargs)


class Account(models.Model):
    AccountID = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    URL = models.TextField()
    Active = models.BooleanField()
    BalanceBroughtForward = models.DecimalField(max_digits=9, decimal_places=2)
    CostCenter = models.TextField()
    CostCenterSettings = models.TextField()
    Description = models.TextField()
    Number = models.IntegerField()
    Project = models.TextField()
    ProjectSettings = models.TextField()
    SRU = models.IntegerField()
    VATCode = models.TextField()
    Year = models.IntegerField()
