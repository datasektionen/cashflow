"""Writes a claim the way Cashflow 3's views do, through its own models and
storage, so Cashflow 4 can be checked reading it."""
import base64, datetime, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cashflow.settings")
import django
django.setup()
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from core.models import Claim, ClaimPart, Comment, File
from expenses.models import ExpenseData, Payment

# A 1x1 PNG: enough for both apps to store, list and serve.
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")

kassor = User.objects.get(username="turetek")
owner = User.objects.get(username="marmed").profile
data = ExpenseData.objects.create(expense_date=datetime.date(2026, 10, 27))
claim = Claim.objects.create(description="Skrivet av Cashflow 3 – öäå", owner=owner, expense_data=data)
parts = [
    ClaimPart.objects.create(claim=claim, cost_centre="Ada", secondary_cost_centre="Internt", budget_line="Fika", amount="99.90"),
    ClaimPart.objects.create(claim=claim, cost_centre="Studienämnden", secondary_cost_centre="Studiesociala", budget_line="Tentapub", amount="0.10"),
]
f = File(claim=claim)
f.file.save("kvitto-från-django.png", ContentFile(PNG), save=True)
for p in parts:
    p.attest(kassor)
claim.refresh_from_db()
claim.confirm(kassor)
Comment.objects.create(author=kassor.profile, claim=claim, content="Kommentar från Cashflow 3")
payment = Payment.objects.create(payer=kassor.profile, receiver=owner)
data.refresh_from_db()
data.reimbursement = payment
data.save(update_fields=["reimbursement"])
claim.refresh_from_db()
claim.account(kassor, voucher_number="M77")
print("NUMBER", claim.data_id, "FILE", f.file.name, "PAYMENT", payment.id)
