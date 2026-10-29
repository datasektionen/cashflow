"""Reads everything in the shared database through Cashflow 3's own models
and serializers, as its API would, and fetches each claim's files through
its storage. Any exception means Cashflow 3 can't show what Cashflow 4 wrote."""
import os, sys, traceback, urllib.request
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cashflow.settings")
import django
django.setup()
from core.models import Claim
from expenses.models import Payment
from expenses.api.serializers import ExpenseAdminSerializer, PaymentSerializer
from invoices.api.serializers import InvoiceSerializer
from core.api.serializers import ClaimSerializer

failures = []
def check(label, fn):
    try:
        return fn()
    except Exception as e:
        failures.append(f"{label}: {type(e).__name__}: {e}")
        traceback.print_exc()

claims = list(Claim.objects.with_total())
for c in claims:
    ser = ExpenseAdminSerializer if c.expense_data_id else InvoiceSerializer
    data = check(f"claim {c.type} {c.data_id}", lambda: ser(c).data)
    check(f"list row {c.type} {c.data_id}", lambda: ClaimSerializer(c).data)
    for f in c.file_set.all():
        def fetch():
            with urllib.request.urlopen(f.file.url) as r:
                assert r.status == 200 and len(r.read()) > 0
        check(f"file {f.file.name}", fetch)
for p in Payment.objects.all():
    check(f"payment {p.id}", lambda: PaymentSerializer(p).data)

uploaded = sum(1 for c in claims for f in c.file_set.all() if f.file.name.startswith("c4/"))
print(f"Cashflow 3 read {len(claims)} claims ({uploaded} files uploaded by Cashflow 4) and {Payment.objects.count()} payments")
for failure in failures:
    print("FAILED", failure)
sys.exit(1 if failures else 0)
