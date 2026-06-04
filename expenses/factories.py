import factory
from factory.django import DjangoModelFactory

from core.factories import ProfileFactory
from expenses.models import Expense, ExpensePart, File


class ExpenseFactory(DjangoModelFactory):
    class Meta:
        model = Expense
        skip_postgeneration_save = True

    owner = factory.SubFactory(ProfileFactory)
    description = factory.Faker("text")
    expense_date = factory.Faker("date")
    file = factory.RelatedFactory(
        "claims.factories.ExpenseFileFactory", factory_related_name="expense"
    )


class ExpenseFileFactory(DjangoModelFactory):
    class Meta:
        model = File

    expense = factory.SubFactory(ExpenseFactory)
    invoice = None
    file = factory.django.FileField()


class ExpensePartFactory(DjangoModelFactory):
    class Meta:
        model = ExpensePart

    expense = factory.SubFactory(ExpenseFactory)
    cost_centre = factory.Faker("word")
    secondary_cost_centre = factory.Faker("word")
    budget_line = factory.Faker("word")
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
