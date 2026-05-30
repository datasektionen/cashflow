import factory
from factory.django import DjangoModelFactory

from core.factories import ProfileFactory
from expenses.models import File
from invoices.models import Invoice, InvoicePart


class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model = Invoice
        skip_postgeneration_save = True

    owner = factory.SubFactory(ProfileFactory)
    description = factory.Faker("text")
    invoice_date = factory.Faker("date")
    due_date = factory.Faker("date")
    file_is_original = True
    file = factory.RelatedFactory(
        "invoices.factories.InvoiceFileFactory", factory_related_name="invoice"
    )


class InvoiceFileFactory(DjangoModelFactory):
    class Meta:
        model = File

    expense = None
    invoice = factory.SubFactory(InvoiceFactory)
    file = factory.django.FileField()


class InvoicePartFactory(DjangoModelFactory):
    class Meta:
        model = InvoicePart

    invoice = factory.SubFactory(InvoiceFactory)
    cost_centre = factory.Faker("word")
    secondary_cost_centre = factory.Faker("word")
    budget_line = factory.Faker("word")
    amount = factory.Faker("pydecimal", left_digits=5, right_digits=2, positive=True)
