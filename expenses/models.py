import re

import requests
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

from cashflow import settings

# represents a bank account owned by the organisation
class BankAccount(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def to_dict(self):
        return model_to_dict(self)


class Profile(models.Model):
    user = models.OneToOneField(User)

    # represents a bank account owned by the user
    bank_account = models.CharField(max_length=13, blank=True)
    sorting_number = models.CharField(max_length=6, blank=True)
    bank_name = models.CharField(max_length=30, blank=True)
    default_account = models.ForeignKey(BankAccount, blank=True, null=True)
    firebase_instance_id = models.TextField(blank=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

    def __unicode__(self):
        return self.user.first_name + " " + self.user.last_name

    def to_dict(self):
        person_dict = model_to_dict(self)
        person_dict['username'] = self.user.username
        person_dict['first_name'] = self.user.first_name
        person_dict['last_name'] = self.user.last_name

        if self.default_account is not None:
            person_dict['default_account'] = self.default_account.to_dict()
        else:
            person_dict['default_account'] = None

        del person_dict['user']
        del person_dict['id']

        return person_dict

    def user_dict(self):
        return {
            'id': self.user.id,
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email
        }

    def may_attest(self):
        may_attest = []
        from cashflow import dauth
        for permission in dauth.get_permissions(self.user):
            if permission.startswith("attest-"):
                may_attest.append(permission[len("attest-"):].lower())
        return may_attest

    def may_pay(self):
        from cashflow import dauth
        return 'pay' in dauth.get_permissions(self.user)

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


class Payment(models.Model):
    date = models.DateField(auto_now_add=True)
    payer = models.ForeignKey(Profile, related_name='payer')
    receiver = models.ForeignKey(Profile, related_name='receiver')
    account = models.ForeignKey(BankAccount)

    def __str__(self):
        return str(self.amount) + " kr on " + str(self.date) + " transferred by " + self.payer.__str__()

    def __unicode__(self):
        return str(self.amount) + " kr on " + str(self.date) + " transferred by " + self.payer.__unicode__()

    def to_dict(self):
        payment = model_to_dict(self)
        payment['payer'] = self.payer.user_dict()
        payment['receiver'] = self.receiver.user_dict()
        payment['account'] = self.account.to_dict()
        return payment

    def amount(self):
        total = 0
        for expense in Expense.objects.filter(reimbursement=self):
            total += expense.total_amount()
        return total

    def tag(self):
        return "Data" + str(self.id)


class Expense(models.Model):
    created_date = models.DateField(auto_now_add=True)
    expense_date = models.DateField()
    owner = models.ForeignKey(Profile)
    description = models.TextField()
    reimbursement = models.ForeignKey(Payment, blank=True, null=True)
    verification = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.description

    def __unicode__(self):
        return self.description

    def __repr__(self):
        return str(self.to_dict())

    def total_amount(self):
        total = 0
        for part in self.expensepart_set.all():
            total += part.amount
        return total

    def committees(self):
        return self.expensepart_set.order_by().values('committee_name').distinct()

    def to_dict(self):
        exp = model_to_dict(self)
        exp['expense_parts'] = [part.to_dict() for part in ExpensePart.objects.filter(expense=self)]
        exp['owner_username'] = self.owner.user.username
        exp['owner_first_name'] = self.owner.user.first_name
        exp['owner_last_name'] = self.owner.user.last_name
        if self.reimbursement is not None:
            exp['reimbursement'] = self.reimbursement.to_dict()
        return exp


class File(models.Model):
    belonging_to = models.ForeignKey(Expense, on_delete=models.CASCADE)
    file = models.FileField()

    def __str__(self):
        return self.file.url

    def __unicode__(self):
        return self.file.url

    def to_dict(self):
        return {
            'url': self.file.url,
            'id': self.id
        }

    def is_image(self):
        file_regex = re.compile(".*\.(jpg|jpeg|png|gif|bmp)",
                                re.IGNORECASE)  # check if file has a known image-file-ending
        return file_regex.match(self.file.name)


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

    def __str__(self):
        return self.expense.__str__() + " (" + self.budget_line_name + ": " + str(self.amount) + " kr)"

    def __unicode__(self):
        return self.expense.__unicode__() + " (" + self.budget_line_name + ": " + str(self.amount) + " kr)"

    def to_dict(self):
        exp_part = model_to_dict(self)
        del exp_part['expense']

        if self.attested_by is not None:
            exp_part['attested_by_username'] = self.attested_by.user.username
            exp_part['attested_by_first_name'] = self.attested_by.user.first_name
            exp_part['attested_by_last_name'] = self.attested_by.user.last_name

        return exp_part


class Comment(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Profile)
    content = models.TextField()

    def __str__(self):
        return self.author.__str__() + " - " + str(self.date) + ": " + self.content

    def __unicode__(self):
        return self.author.__unicode__() + " - " + \
               str(self.date) + ": " + self.content

    def to_dict(self):
        comment = model_to_dict(self)
        comment['author_username'] = self.author.user.username
        comment['author_first_name'] = self.author.user.first_name
        comment['author_last_name'] = self.author.user.last_name
        return comment


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
