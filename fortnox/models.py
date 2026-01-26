from django.db import models


class AuthToken(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()

    
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

