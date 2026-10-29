#!/usr/bin/env python3
"""Parity test: asks Cashflow 3 and Cashflow 4 the same questions about the
same database, as each user, and lists every answer that differs.

Cashflow 3 answers from its own code (cashflow3.py, run in its Docker image).
Cashflow 4 answers through its API (the dev server on :3000), logged in through
the mock SSO. Differences that are deliberate (KNOWN, with the reason) are
reported separately; any other difference fails the run.

    make services dev-server   # then:
    make parity
"""
import datetime
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

GO = os.environ.get("CASHFLOW_URL", "http://localhost:3000")
USERS = ["turetek", "diadat", "marmed", "jobjav", "sauron", "bilbek"]
TODAY = datetime.date.today()
YEAR = TODAY.year
PERIODS = {"all": "", "year": f"{YEAR}-01-01", "month": TODAY.replace(day=1).isoformat()}
GO_PERIOD = {"all": "PERIOD_ALL_TIME", "year": "PERIOD_YEAR", "month": "PERIOD_MONTH"}
# Cashflow 3's list filters, and the same question in Cashflow 4's terms.
FILTERS = {
    "attested": ({"attested": "true"}, {"attested": True}),
    "not attested": ({"attested": "false"}, {"attested": False}),
    "confirmed": ({"confirmed": "true"}, {"confirmed": True}),
    "not confirmed": ({"confirmed": "false"}, {"confirmed": False}),
    "paid": ({"paid": "true"}, {"paid": True}),
    "not paid": ({"paid": "false"}, {"paid": False}),
    "accounted": ({"accounted": "true"}, {"accounted": True}),
    "flagged": ({"flagged": "true"}, {"flagged": True}),
    "not flagged": ({"flagged": "false"}, {"flagged": False}),
    "owner bilbek": ({"user": "bilbek"}, {"owner": "bilbek"}),
    "cost centre Ada": ({"cost_centre": "Ada"}, None),
}

# Differences that are on purpose, or Cashflow 3 failing. Each is matched by
# a pattern on the difference's path (and optionally Cashflow 3's answer) and
# explained in the report.
KNOWN = [
    (r"/actions/", "crash",
     "Cashflow 3 crashes (500): its visibility filter joins the parts without DISTINCT, so for anyone but admins, "
     "payers and confirmers a claim with two or more parts comes back twice and get_object() fails. Cashflow 4 works."),
    (r"/actions/[ei]\d+/(un)?flag$", True,
     "Cashflow 3 accepts flagging a flagged expense (and unflagging one that isn't) as a no-op; Cashflow 4 only "
     "offers the action that changes something."),
    (r"filters/attested$", None,
     "Cashflow 3's attested=true matches claims with any attested part; Cashflow 4 means every part attested, "
     "which is what the stage 'Attesterat' says."),
    (r"filters/(not )?confirmed$", None,
     "Cashflow 3 lets every invoice through the confirmed filter, both ways; in Cashflow 4 it is about expenses only, "
     "the claims with a receipt to confirm."),
]


class Rewrite(urllib.request.HTTPRedirectHandler):
    """The mock SSO sends the browser back to the web dev server (:5173);
    in this test the API server takes the callback itself."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, newurl.replace("localhost:5173", GO.split("//")[1]))


def login(username):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), Rewrite())
    page = opener.open(f"{GO}/login")
    request_id = urllib.parse.parse_qs(urllib.parse.urlparse(page.url).query)["authRequestID"][0]
    opener.open("http://localhost:7003/login", urllib.parse.urlencode({"id": request_id, "kthid": username}).encode())

    def call(method, body):
        req = urllib.request.Request(f"{GO}/api/{method}", json.dumps(body).encode(),
                                     {"Content-Type": "application/json", "Origin": GO})
        with opener.open(req) as r:
            return json.load(r)

    call("cashflow.user.v1.UserService/GetMe", {})
    return call


def ref(summary):
    return ("e" if summary["kind"] == "CLAIM_KIND_EXPENSE" else "i") + summary["number"]


def go_claims(call, **request):
    out, page = [], 1
    while True:
        try:
            r = call("cashflow.claim.v1.ClaimService/ListClaims", {**request, "page": page, "pageSize": 100})
        except urllib.error.HTTPError as e:
            # A queue the user may not see is refused; Cashflow 3 lists nothing.
            if e.code == 403:
                return []
            raise
        out += [ref(c) for c in r.get("claims", [])]
        if page * 100 >= r.get("total", 0):
            return sorted(set(out))
        page += 1


def go_side():
    result = {"users": {}}
    for username in USERS:
        call = login(username)
        visible = go_claims(call)
        queues = {q: go_claims(call, queue=f"QUEUE_{q.upper()}") for q in ["attest", "confirm", "account", "pay"]}
        overview = {"attest": {}, "confirm": {}, "account": {}, "pay": {}}
        for q in call("cashflow.claim.v1.ClaimService/GetWorkOverview", {}).get("queues", []):
            overview[q["queue"].removeprefix("QUEUE_").lower()] = {g["key"]: g["count"] for g in q.get("groups", [])}
        actions = {}
        for r in visible:
            kind = "CLAIM_KIND_EXPENSE" if r[0] == "e" else "CLAIM_KIND_INVOICE"
            a = call("cashflow.claim.v1.ClaimService/GetClaim", {"kind": kind, "number": r[1:]})["claim"]["actions"]
            actions[r] = {
                "attest": sorted(int(i) for i in a.get("attestPartIds", [])),
                "unattest": sorted(int(i) for i in a.get("unattestPartIds", [])),
                **{k: bool(a.get(k)) for k in ["confirm", "unconfirm", "flag", "unflag", "pay", "delete", "edit", "account"]},
            }
        result["users"][username] = {
            "visible": visible,
            "queues": queues,
            "overview": overview,
            "filters": {name: go_claims(call, filter=f) if f is not None else go_claims(call, costCentre="Ada")
                        for name, (_, f) in FILTERS.items()},
            "actions": actions,
            "personal": {p: call("cashflow.stats.v1.StatsService/GetPersonalStats", {"username": username, "period": GO_PERIOD[p]})
                         for p in PERIODS},
        }
    call = login(USERS[0])
    result["year"] = call("cashflow.stats.v1.StatsService/GetYear", {"year": YEAR})
    result["leaderboard"] = {
        f"{p}/{o}": call("cashflow.stats.v1.StatsService/GetLeaderboard",
                         {"period": GO_PERIOD[p], "ranking": "RANKING_COUNT" if o.endswith("count") else "RANKING_TOTAL"}).get("entries", [])
        for p in PERIODS for o in ["-expense_total", "-expense_count"]
    }
    tree = call("cashflow.budget.v1.BudgetService/GetBudget", {"year": YEAR}).get("costCentres", [])
    lines = {}
    for cc in tree:
        for scc in cc.get("secondary", []):
            for line in scc.get("lines", []):
                amounts = [int(line.get(k, 0)) for k in ("usedOre", "attestedOre", "paidOre")] + [bool(line.get("blown"))]
                if any(amounts):
                    lines[f"{cc['name']} / {scc['name']} / {line['name']}"] = amounts
    result["budget"] = {"lines": lines, "blown": sorted(cc["name"] for cc in tree if cc.get("containsBlown"))}
    return result


def django_side():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = {
        "PARITY_USERS": json.dumps(USERS),
        "PARITY_FILTERS": json.dumps({name: params for name, (params, _) in FILTERS.items()}),
        "PARITY_YEAR": str(YEAR),
        "PARITY_PERIODS": json.dumps(PERIODS),
    }
    cmd = ["docker", "run", "--rm", "--network", "host", "-v", f"{root}/scripts/parity:/parity:ro", "-e", "PYTHONPATH=/app",
           "-e", "DB_HOST=localhost", "-e", "DB_PORT=5433", "-e", "DEBUG=True", "-e", "DJANGO_LOG_LEVEL=ERROR",
           "-e", "SECRET_KEY=x", "-e", "OIDC_PROVIDER=http://localhost:7003", "-e", "OIDC_ID=x", "-e", "OIDC_SECRET=x",
           "-e", "HIVE_URL=http://localhost:7004", "-e", "HIVE_SECRET=dev", "-e", "FORTNOX_ENABLED=false",
           *[x for k, v in env.items() for x in ("-e", f"{k}={v}")],
           "cashflow3-base", "poetry", "run", "python", "/parity/cashflow3.py"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"PARITY-JSON-BEGIN\n(.*)\nPARITY-JSON-END", out.stdout, re.S)
    if not m:
        sys.exit("Cashflow 3 gave no answer:\n" + out.stdout[-3000:] + out.stderr[-3000:])
    return json.loads(m.group(1))


def ore(kronor):
    return round(float(kronor) * 100)


def normalise(c3, c4):
    """Puts both sides' stats in one shape: (username, öre, count) and per month."""
    for side, users in [("c3", c3["users"]), ("c4", c4["users"])]:
        for u in users.values():
            for p, s in u["personal"].items():
                if side == "c3":
                    u["personal"][p] = {"total": ore(s.get("expense_total", 0)), "count": s.get("expense_count", 0),
                                        "total_rank": s.get("amount_rank") or 0, "count_rank": s.get("count_rank") or 0}
                else:
                    u["personal"][p] = {"total": int(s.get("totalOre", 0)), "count": s.get("count", 0),
                                        "total_rank": s.get("totalRank", 0), "count_rank": s.get("countRank", 0)}
    c3["year"] = [(m["month"], m["expense_count"], ore(m["expense_total"]), m["invoice_count"], ore(m["invoice_total"]))
                  for m in c3["year"]["months"]]
    c4["year"] = [(m["month"], m.get("expenseCount", 0), int(m.get("expenseTotalOre", 0)), m.get("invoiceCount", 0),
                   int(m.get("invoiceTotalOre", 0))) for m in c4["year"]["months"]]
    c3["budget"]["lines"] = {k: [ore(v[0]), ore(v[1]), ore(v[2]), bool(v[3])] for k, v in c3["budget"]["lines"].items()}
    for k in c3["leaderboard"]:
        c3["leaderboard"][k] = [(e["owner"]["username"], ore(e["expense_total"]), e["expense_count"]) for e in c3["leaderboard"][k]]
        c4["leaderboard"][k] = [(e["person"]["username"], int(e.get("totalOre", 0)), e.get("count", 0)) for e in c4["leaderboard"][k]]


def diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            yield from diff(a.get(k), b.get(k), f"{path}/{k}")
    elif a != b:
        yield path, a, b


def leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from leaves(v)
    else:
        yield value


def main():
    print("Asking Cashflow 4 …", file=sys.stderr)
    c4 = go_side()
    print("Asking Cashflow 3 …", file=sys.stderr)
    c3 = django_side()
    normalise(c3, c4)
    known, unknown = [], []
    for path, a, b in diff(c3, c4):
        reason = next((why for pattern, c3_answer, why in KNOWN
                       if re.search(pattern, path) and (c3_answer is None or a == c3_answer)), None)
        (known if reason else unknown).append((path, a, b, reason))
    for title, items in [("Deliberate differences", known), ("Differences", unknown)]:
        print(f"\n{title}: {len(items)}")
        for path, a, b, reason in items:
            print(f"  {path}\n    Cashflow 3: {a}\n    Cashflow 4: {b}")
    compared = sum(1 for _ in leaves(c3))
    print(f"\n{compared} answers compared, {len(unknown)} unexplained differences, {len(known)} deliberate")
    sys.exit(1 if unknown else 0)


if __name__ == "__main__":
    main()
