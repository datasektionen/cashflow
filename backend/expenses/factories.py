import factory
from factory.django import DjangoModelFactory

from core.factories import ProfileFactory
from core.models import Claim, ClaimPart, File
from expenses.models import ExpenseData, Payment


class ExpenseDataFactory(DjangoModelFactory[ExpenseData]):
    class Meta:
        model = ExpenseData

    expense_date = factory.Faker("date_object")


class ExpenseFactory(DjangoModelFactory[Claim]):
    """An expense claim with one file and one part.

    Expense-specific fields live on the related ExpenseData, so set them with
    e.g. `ExpenseFactory(expense_data__is_flagged=True)`. The API addresses
    expenses by `claim.data_id`, not `claim.id`.
    """

    class Meta:
        model = Claim
        skip_postgeneration_save = True

    owner = factory.SubFactory(ProfileFactory)
    description = factory.Faker("text")
    expense_data = factory.SubFactory(ExpenseDataFactory)
    file = factory.RelatedFactory(
        "expenses.factories.ExpenseFileFactory", factory_related_name="claim"
    )
    part = factory.RelatedFactory(
        "expenses.factories.ExpensePartFactory", factory_related_name="claim"
    )


class ExpenseFileFactory(DjangoModelFactory[File]):
    class Meta:
        model = File

    claim = factory.SubFactory(ExpenseFactory)
    file = factory.django.FileField()


class PaymentFactory(DjangoModelFactory[Payment]):
    class Meta:
        model = Payment

    payer = factory.SubFactory(ProfileFactory)
    receiver = factory.SubFactory(ProfileFactory)


class ExpensePartFactory(DjangoModelFactory[ClaimPart]):
    class Meta:
        model = ClaimPart

    claim = factory.SubFactory(ExpenseFactory)
    cost_centre = factory.Faker("word")
    secondary_cost_centre = factory.Faker("word")
    budget_line = factory.Faker("word")
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
