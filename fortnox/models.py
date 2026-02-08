from django.contrib.auth.models import User
from django.db import models


class APIUser(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name="fortnox")
    name = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    access_token = models.TextField(null=False)
    refresh_token = models.TextField(null=False)


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
