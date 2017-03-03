from django.db import models
from django.contrib.auth.models import User as AuthUser

# Create your models here.


class Committee(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name

class CostCentre(models.Model):
    committee = models.ForeignKey(Committee)
    name = models.TextField()

    def __str__(self):
        return self.committee.__str__() + " -> " + self.name

class BudgetLine(models.Model):
    cost_centre = models.ForeignKey(CostCentre)
    name = models.TextField()

    def __str__(self):
        return self.cost_centre.__str__() + " -> " + self.name


class BankAccount(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name


class Person(models.Model):
    user = models.OneToOneField(AuthUser)
    bank_account = models.CharField(max_length=10,blank=True)
    sorting_number = models.CharField(max_length=6,blank=True)
    bank_name = models.CharField(max_length=30,blank=True)
    default_account = models.ForeignKey(BankAccount, blank=True, null=True)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name

class Payment(models.Model):
    date = models.DateField()
    payer = models.ForeignKey(Person)
    amount = models.IntegerField()
    account = models.ForeignKey(BankAccount)

    def __str__(self):
        return str(self.amount) + " kr on " + self.date + " transfered by " + self.payer.__str__()

class Expense(models.Model):
    expense_date = models.DateField()
    owner = models.ForeignKey(Person)
    description = models.TextField()
    reimbursement = models.ForeignKey(Payment, blank=True, null=True)
    verification = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.description


class File(models.Model):
    belonging_to = models.ForeignKey(Expense)
    file_path = models.FilePathField()

    def __str__(self):
        return self.file_path


class ExpensePart(models.Model):
    expense = models.ForeignKey(Expense)
    budget_line = models.ForeignKey(BudgetLine)
    amount = models.IntegerField()
    attested_by = models.ForeignKey(Person, blank=True, null=True)
    attest_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.file_path


class Comment(models.Model):
    expense = models.ForeignKey(Expense)
    date = models.DateField()
    author = models.ForeignKey(Person)
    content = models.TextField()

    def __str__(self):
        return self.author.__str__() + " - " + self.date + ": " + self.comment



