import factory
from factory.django import DjangoModelFactory

from core.factories import ProfileFactory
from core.models import Claim, ClaimPart, File
from invoices.models import InvoiceData


class InvoiceDataFactory(DjangoModelFactory[InvoiceData]):
    class Meta:
        model = InvoiceData

    invoice_date = factory.Faker("date_object")
    invoice_number = factory.Faker("numerify", text="#######")
    due_date = factory.Faker("date_object")


class InvoiceFactory(DjangoModelFactory[Claim]):
    """An invoice claim with one file and no parts.

    Invoice-specific fields live on the related InvoiceData, so set them with
    e.g. `InvoiceFactory(invoice_data__invoice_date=...)`. The API addresses
    invoices by `claim.data_id`, not `claim.id`.
    """

    class Meta:
        model = Claim
        skip_postgeneration_save = True

    owner = factory.SubFactory(ProfileFactory)
    description = factory.Faker("text")
    invoice_data = factory.SubFactory(InvoiceDataFactory)
    file = factory.RelatedFactory(
        "invoices.factories.InvoiceFileFactory", factory_related_name="claim"
    )


class InvoiceFileFactory(DjangoModelFactory[File]):
    class Meta:
        model = File

    claim = factory.SubFactory(InvoiceFactory)
    file = factory.django.FileField()


class InvoicePartFactory(DjangoModelFactory[ClaimPart]):
    class Meta:
        model = ClaimPart

    claim = factory.SubFactory(InvoiceFactory)
    cost_centre = factory.Faker("word")
    secondary_cost_centre = factory.Faker("word")
    budget_line = factory.Faker("word")
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
