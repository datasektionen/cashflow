from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("expenses", "0034_remove_expense_confirmed_by_remove_expense_owner_and_more"),
        # Invoice/InvoicePart reference expenses.Profile, delete them before it
        ("invoices", "0007_remove_invoicepart_invoice_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Profile",
        ),
    ]
