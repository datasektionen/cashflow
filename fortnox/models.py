from django.db import models
from django.contrib.auth.models import User


class APITokens(models.Model):
    user = models.ForeignKey(User, primary_key=True, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True)
    access_token = models.TextField()
    refresh_token = models.TextField()


    @classmethod
    def from_auth_response(cls, user, data):
        return cls.objects.update_or_create(
            user = user,
            # access_token=data['access_token'],
            # refresh_token=data['refresh_token'],
            defaults={
                'access_token': data['access_token'],
                'refresh_token': data['refresh_token'],
            }
        )
    
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

