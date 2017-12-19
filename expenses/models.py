import re

import requests
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

from cashflow import settings

"""

Defines all the models of the app.

"""

"""
BankAccount represents an actual bank account owned by the organisation.
This is a real bank account like one on Handelsbanken or another bank.
"""
class BankAccount(models.Model):
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



"""
A profile is attached to each user to be able to store more information
and relations with it.
"""
class Profile(models.Model):
    # The relation to the original django user
    user = models.OneToOneField(User)

    # Represents a bank account owned by the user
    bank_account = models.CharField(max_length=13, blank=True)
    
    sorting_number = models.CharField(max_length=6, blank=True)
    bank_name = models.CharField(max_length=30, blank=True)
    default_account = models.ForeignKey(BankAccount, blank=True, null=True)
    firebase_instance_id = models.TextField(blank=True)

    # Return a string representation of the user
    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

    # Return a unicode representation of the user
    def __unicode__(self):
        return self.user.first_name + " " + self.user.last_name

    # Creates a dict from the model
    def to_dict(self):
        person_dict = model_to_dict(self)
        person_dict['username'] = self.user.username
        person_dict['first_name'] = self.user.first_name
        person_dict['last_name'] = self.user.last_name
        person_dict['bank_info']['bank_account'] = self.bank_account
        person_dict['bank_info']['sorting_number'] = self.sorting_number
        person_dict['bank_info']['bank_name'] = self.bank_name
        if self.default_account is not None:
            person_dict['default_account'] = self.default_account.to_dict()
        else:
            person_dict['default_account'] = None
        del person_dict['user']
        del person_dict['id']
        return person_dict

    # Creates and returns an object with the user's properties
    def user_dict(self):
        return {
            'id': self.user.id,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'bank_info': {
                'bank_account': self.bank_account,
                'sorting_number': self.sorting_number,
                'bank_name': self.bank_name
            }
        }

    # Returns a list of the committees that the user may attest
    def may_attest(self):
        may_attest = []
        from cashflow import dauth
        for permission in dauth.get_permissions(self.user):
            if permission.startswith("attest-"):
                may_attest.append(permission[len("attest-"):].lower())
        return may_attest

    # Returns a list of the committees that the user may pay for
    def may_pay(self):
        from cashflow import dauth
        return 'pay' in dauth.get_permissions(self.user)

    # Returns a list of the committees that the user may pay for
    def may_confirm(self):
        from cashflow import dauth
        return 'confirm' in dauth.get_permissions(self.user)

    # Returns a list of the committees that the user may account for
    def may_account(self):
        may_account = []
        from cashflow import dauth
        for permission in dauth.get_permissions(self.user):
            if permission.startswith("accounting-"):
                may_account.append(permission[len("accounting-"):].lower())
        return may_account


# Based of https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()



"""
Represents a payment from a chapter account to a member.
"""
class Payment(models.Model):
    date = models.DateField(auto_now_add=True)
    payer = models.ForeignKey(Profile, related_name='payer')
    receiver = models.ForeignKey(Profile, related_name='receiver')
    account = models.ForeignKey(BankAccount)

    # Return a string representation of the payment
    def __str__(self):
        return str(self.amount) + " kr on " + str(self.date) + " transferred by " + self.payer.__str__()

    # Return a unicode representation of the payment
    def __unicode__(self):
        return str(self.amount) + " kr on " + str(self.date) + " transferred by " + self.payer.__unicode__()

    # Return a dict from the model
    def to_dict(self):
        payment = model_to_dict(self)
        payment['payer'] = self.payer.user_dict()
        payment['receiver'] = self.receiver.user_dict()
        payment['account'] = self.account.to_dict()
        payment['tag'] = self.tag()
        payment['amount'] = self.amount()
        return payment

    # Returns the total amount of the payment
    def amount(self):
        total = 0
        for expense in Expense.objects.filter(reimbursement=self):
            total += expense.total_amount()
        return total

    # Returns the payment tag, which makes the payment identifiable in the bank
    def tag(self):
        return "Data" + str(self.id)



"""
Represents an expense. An expense contains expense parts and information 
about the expense.
"""
class Expense(models.Model):
    created_date = models.DateField(auto_now_add=True)
    expense_date = models.DateField()
    confirmed_by = models.ForeignKey(User, blank=True, null=True)
    confirmed_at = models.DateField(blank=True, null=True, default=None)
    owner = models.ForeignKey(Profile)
    description = models.TextField()
    reimbursement = models.ForeignKey(Payment, blank=True, null=True)
    verification = models.CharField(max_length=7, blank=True)

    # Returns a string representation of the expense
    def __str__(self):
        return self.description

    # Returns a unicode representation of the expense
    def __unicode__(self):
        return self.description

    # Returns a json dict from the expense
    def __repr__(self):
        return str(self.to_dict())

    # Return the total amount of the expense parts
    def total_amount(self):
        total = 0
        for part in self.expensepart_set.all():
            total += part.amount
        return total

    # Returns the committees belonging to the expense as a list [{ committee_name: 'Name' }, ...]
    def committees(self):
        return self.expensepart_set.order_by('committee_name').values('committee_name').distinct()

    # Returns a dict representation of the model
    def to_dict(self):
        exp = model_to_dict(self)
        exp['expense_parts'] = [part.to_dict() for part in ExpensePart.objects.filter(expense=self)]
        exp['owner_username'] = self.owner.user.username
        exp['owner_first_name'] = self.owner.user.first_name
        exp['owner_last_name'] = self.owner.user.last_name
        exp['amount'] = self.total_amount()
        exp['committees'] = [committee['committee_name'] for committee in self.committees()]
        if self.reimbursement is not None:
            exp['reimbursement'] = self.reimbursement.to_dict()
        return exp


"""
Represents a file on, for example, S3.
"""
class File(models.Model):
    belonging_to = models.ForeignKey(Expense, on_delete=models.CASCADE)
    file = models.FileField()

    # Returns a string representation of the file
    def __str__(self):
        return self.file.url

    # Returns a unicode representation of the file
    def __unicode__(self):
        return self.file.url

    # Returns a dict representation of the file
    def to_dict(self):
        return {
            'url': self.file.url,
            'id': self.id
        }

    # Returns true if image url ends with commit image file names
    def is_image(self):
        file_regex = re.compile(".*\.(jpg|jpeg|png|gif|bmp)", re.IGNORECASE)
        return file_regex.match(self.file.name)



"""
Defines an expense part, which is a specification of a part of an expense.
"""
class ExpensePart(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    budget_line_id = models.IntegerField(default=0)
    budget_line_name = models.TextField(blank=True)
    cost_centre_name = models.TextField(blank=True)
    cost_centre_id = models.IntegerField(default=0)
    committee_name = models.TextField(blank=True)
    committee_id = models.IntegerField(default=0)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey(Profile, blank=True, null=True)
    attest_date = models.DateField(blank=True, null=True)

    # Returns string representation of the model
    def __str__(self):
        return self.expense.__str__() + " (" + self.budget_line_name + ": " + str(self.amount) + " kr)"

    # Returns unicode representation of the model
    def __unicode__(self):
        return self.expense.__unicode__() + " (" + self.budget_line_name + ": " + str(self.amount) + " kr)"

    # Returns dict representation of the model
    def to_dict(self):
        exp_part = model_to_dict(self)
        del exp_part['expense']
        if self.attested_by is not None:
            exp_part['attested_by_username'] = self.attested_by.user.username
            exp_part['attested_by_first_name'] = self.attested_by.user.first_name
            exp_part['attested_by_last_name'] = self.attested_by.user.last_name
        return exp_part


"""
Represents a comment on an expense.
"""
class Comment(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Profile)
    content = models.TextField()

    # String representation of comment
    def __str__(self):
        return self.author.__str__() + " - " + str(self.date) + ": " + self.content

    # Unicode representation of comment
    def __unicode__(self):
        return self.author.__unicode__() + " - " + \
               str(self.date) + ": " + self.content

    # Dict representation of the comment
    def to_dict(self):
        comment = model_to_dict(self)
        comment['author_username'] = self.author.user.username
        comment['author_first_name'] = self.author.user.first_name
        comment['author_last_name'] = self.author.user.last_name
        return comment

# Sends mail on comment
@receiver(post_save, sender=Comment)
def send_mail(sender, instance, created, *args, **kwargs):
    if sender == Comment:
        if created and instance.author != instance.expense.owner:
            requests.post("http://spam.datasektionen.se/api/sendmail", json={
                'from': 'no-reply@datasektionen.se',
                'to': instance.expense.owner.user.email,
                'subject': str(instance.author) + ' har lagt till en kommentar på ditt utlägg.',
                'content': render_to_string("email.html", {'comment': instance, 'receiver': instance.expense.owner}),
                'key': settings.SPAM_API_KEY
            })
