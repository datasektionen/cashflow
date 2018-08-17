from django.db import models

# Create your models here.
from django.forms import model_to_dict


class BankAccount(models.Model):
    """
    BankAccount represents an actual bank account owned by the organisation.
    This is a real bank account like one on Handelsbanken or another bank.
    """
    name = models.TextField()

    # Return a string representation of the bank account
    def __str__(self):
        return self.name

    # Return a unicode representation of the bank account
    def __unicode__(self):
        return self.name

    # Creates a dict from the model
    def to_dict(self):
        return model_to_dict(self)
