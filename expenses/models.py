import requests
from channels import Group
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_init, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict

from cashflow.settings import FCM_API_KEY


def get_budget_json():
    budget = {}
    for committee in Committee.objects.all().order_by('name'):
        budget[str(committee.name)] = {}
        for cost_centre in CostCentre.objects.filter(committee=committee).order_by('name'):
            budget[str(committee.name)][str(cost_centre.name)] = []
            for budget_line in BudgetLine.objects.filter(cost_centre=cost_centre).order_by('name'):
                budget[str(committee.name)][str(cost_centre.name)].append(str(budget_line.name))
    j = str(budget)
    return j


class Committee(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    def get_overview_dict(self):
        return {
            'committee_id': self.id,
            'committee_name': self.name,
            'cost_centres': [
                cost_centre.get_overview_dict() for cost_centre in CostCentre.objects.filter(committee=self.id).all()
            ]
        }

    def to_dict(self):
        return {
            'committee_id': self.id,
            'committee_name': self.name,
        }


class CostCentre(models.Model):
    committee = models.ForeignKey(Committee)
    name = models.TextField()

    def __str__(self):
        return self.committee.__str__() + " -> " + self.name

    def __unicode__(self):
        return self.committee.__unicode__() + " -> " + self.name

    def get_overview_dict(self):
        return {
            'cost_centre_id': self.id,
            'cost_centre_name': self.name,
            'budget_lines': [budget_line.get_overview_dict() for budget_line in
                             BudgetLine.objects.filter(cost_centre=self.id).all()]
        }

    def to_dict(self):
        return {
            'cost_centre_id': self.id,
            'cost_centre_name': self.name,
            'committee': self.committee.to_dict()
        }


class BudgetLine(models.Model):
    cost_centre = models.ForeignKey(CostCentre)
    name = models.TextField()

    def __str__(self):
        return self.cost_centre.__str__() + " -> " + self.name

    def __unicode__(self):
        return self.cost_centre.__unicode__() + " -> " + self.name

    def get_overview_dict(self):
        return {
            'budget_line_id': self.id,
            'budget_line_name': self.name
        }

    def to_dict(self):
        return {
            'budget_line_id': self.id,
            'budget_line_name': self.name,
            'cost_centre': self.cost_centre.to_dict()
        }


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


# Based of https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html#onetoone
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Payment(models.Model):
    date = models.DateField()
    payer = models.ForeignKey(Profile, related_name='payer')
    receiver = models.ForeignKey(Profile, related_name='receiver')
    amount = models.IntegerField()
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


class Expense(models.Model):
    expense_date = models.DateField()
    owner = models.ForeignKey(Profile)
    description = models.TextField()
    reimbursement = models.ForeignKey(Payment, blank=True, null=True)
    verification = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.description

    def __unicode__(self):
        return self.description

    def compute_total(self):
        total = 0
        for part in self.expensepart_set.all():
            total += part.amount
        return total

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
    belonging_to = models.ForeignKey(Expense)
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


class ExpensePart(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    budget_line = models.ForeignKey(BudgetLine)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    attested_by = models.ForeignKey(Profile, blank=True, null=True)
    attest_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.expense.__str__() + " (" + self.budget_line.__str__() + ": " + str(self.amount) + " kr)"

    def __unicode__(self):
        return self.expense.__unicode__() + " (" + self.budget_line.__unicode__() + ": " + str(self.amount) + " kr)"

    def to_dict(self):
        exp_part = model_to_dict(self)
        del exp_part['expense']
        exp_part['budget_line'] = self.budget_line.to_dict()

        if self.attested_by is not None:
            exp_part['attested_by_username'] = self.attested_by.user.username
            exp_part['attested_by_first_name'] = self.attested_by.user.first_name
            exp_part['attested_by_last_name'] = self.attested_by.user.last_name

        return exp_part


# noinspection PyUnusedLocal
def send_notification(sender, instance, **kwargs):
    if isinstance(instance, ExpensePart):
        exp = instance.expense
    else:
        exp = instance
    if exp.owner.firebase_instance_id is not "":
        req = requests.post('https://fcm.googleapis.com/fcm/send', json={
            "notification": {
                "title": "Uppdaterat kvitto",
                "body": "Ditt kvitto \"" + str(exp.description) + "\" har uppdaterats"
            },
            "to": exp.owner.firebase_instance_id
        }, headers={
            "Authorization": "key=" + FCM_API_KEY,
            "Content-type": "application/json"
        })


post_save.connect(send_notification, sender=ExpensePart)
post_save.connect(send_notification, sender=Expense)


class Comment(models.Model):
    expense = models.ForeignKey(Expense)
    date = models.DateField()
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


# noinspection PyUnusedLocal
def comment_created(sender, instance, **kwargs):
    Group('cashflow-expense-' + str(instance.expense.id)).send({'comment': instance.to_dict()})


post_init.connect(comment_created, sender=Comment)
