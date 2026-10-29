"""Cashflow 3's answers for the parity test (scripts/parity.py), from its own
code: the API views through DRF's test client, as each user, and every
workflow action tried for real inside a transaction that is rolled back.
Prints one JSON document between markers; the database is left unchanged."""
import json
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cashflow.settings")
import django

django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.test import APIClient

from core.models import Claim

settings.ALLOWED_HOSTS = ["*"]
USERS = json.loads(os.environ["PARITY_USERS"])
FILTERS = json.loads(os.environ["PARITY_FILTERS"])
YEAR = int(os.environ["PARITY_YEAR"])
PERIODS = json.loads(os.environ["PARITY_PERIODS"])


def ref(c):
    return f"{c['type'][0]}{c['id']}"


def claims(client, params=None):
    out, page = [], 1
    while True:
        r = client.get("/api/claims/", {**(params or {}), "per_page": 100, "page": page})
        assert r.status_code == 200, (r.status_code, r.content[:300])
        body = r.json()
        out += [ref(c) for c in body["data"]]
        if page >= body["pagination"]["total_pages"]:
            return sorted(set(out))
        page += 1


def tried(client, method, url, data=None):
    """Whether Cashflow 3 lets the user do it, without keeping the change;
    "crash" when it fails with a server error instead of answering."""
    with transaction.atomic():
        response = getattr(client, method)(url, data or {}, format="json")
        transaction.set_rollback(True)
    if response.status_code >= 500:
        return "crash"
    return 200 <= response.status_code < 300


def actions(client, claim):
    kind = "expenses" if claim.type == "expense" else "invoices"
    base = f"/api/{kind}/{claim.data_id}/"
    parts = list(claim.parts.all())
    a = {
        "attest": sorted(p.id for p in parts if p.attested_by_id is None and tried(client, "post", f"/api/claim-parts/{p.id}/attest/") is True),
        "unattest": sorted(p.id for p in parts if p.attested_by_id is not None and tried(client, "post", f"/api/claim-parts/{p.id}/unattest/") is True),
        "delete": tried(client, "delete", base),
        "edit": tried(client, "patch", base, {"description": claim.description}),
        "account": tried(client, "post", base + "account/", {"voucher_number": "Z1"}),
    }
    if claim.type == "expense":
        a.update(
            confirm=tried(client, "post", base + "confirm/"),
            unconfirm=tried(client, "post", base + "unconfirm/"),
            flag=tried(client, "post", base + "flag/"),
            unflag=tried(client, "post", base + "unflag/"),
            pay=False,
        )
    else:
        a.update(confirm=False, unconfirm=False, flag=False, unflag=False, pay=tried(client, "post", base + "pay/"))
    return a


result = {"users": {}}
all_claims = list(Claim.objects.all())
for username in USERS:
    user = User.objects.filter(username=username).first()
    if user is None:
        continue
    client = APIClient()
    client.force_authenticate(user)
    visible = claims(client)
    queues = {q: claims(client, {f"{name}": "true"}) for q, name in
              [("attest", "attestable"), ("confirm", "confirmable"), ("account", "accountable"), ("pay", "payable")]}
    overview = client.get("/api/actions/overview/").json()
    result["users"][username] = {
        "visible": visible,
        "queues": queues,
        "overview": {
            "attest": {r["cost_centre"]: r["count"] for r in overview["attest"]},
            "confirm": {r["cost_centre"]: r["count"] for r in overview["confirm"]},
            "account": {r["cost_centre"]: r["count"] for r in overview["account"]},
            "pay": {r["username"]: r["count"] for r in overview["pay"]},
        },
        "filters": {name: claims(client, params) for name, params in FILTERS.items()},
        "actions": {f"{c.type[0]}{c.data_id}": actions(client, c) for c in all_claims if f"{c.type[0]}{c.data_id}" in visible},
        "personal": {
            period: client.get(f"/api/stats/leaderboard/{username}/", {"start_date": start} if start else {}).json()
            for period, start in PERIODS.items()
        },
    }

client = APIClient()
client.force_authenticate(User.objects.get(username=USERS[0]))
result["year"] = client.get(f"/api/stats/yearly/{YEAR}/").json()
result["leaderboard"] = {
    f"{period}/{ordering}": client.get(
        "/api/stats/leaderboard/", {"per_page": 20, "ordering": ordering, **({"start_date": start} if start else {})}
    ).json()["data"]
    for period, start in PERIODS.items()
    for ordering in ["-expense_total", "-expense_count"]
}
# The budget: every line's amounts this year, and which cost centres are blown.
budget = {}
blown = []
ccs = client.get("/api/cost-centres/", {"per_page": 100}).json()
for cc in ccs["data"] if isinstance(ccs, dict) else ccs:
    if not cc.get("active"):
        continue
    if cc.get("contains_blown"):
        blown.append(cc["name"])
    detail = client.get(f"/api/cost-centres/{cc['id']}/", {"year": YEAR}).json()
    for scc in detail["secondary_cost_centres"]:
        for line in scc["budget_lines"]:
            amounts = (line["amount_uploaded"], line["amount_attested"], line["amount_paid"], line["blown"])
            if any(a not in ("0.00", "0", False, None) for a in amounts):
                budget[f"{cc['name']} / {scc['name']} / {line['name']}"] = amounts
result["budget"] = {"lines": budget, "blown": sorted(blown)}
print("PARITY-JSON-BEGIN")
print(json.dumps(result, default=str))
print("PARITY-JSON-END")
