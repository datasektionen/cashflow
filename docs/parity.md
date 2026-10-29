# Feature parity with Cashflow 3

Every feature of Cashflow 3 (`backend/`, `frontend/`) and where Cashflow 4 has it. Each phase ticks off its rows;
nothing is dropped without a row saying so and why. Source: the DRF views and serializers, the SvelteKit routes, and
`cashflow/spam.py` as of the `slop-rewrite` branch point.

Legend: ✅ done · 🔜 planned (phase) · ➖ intentionally not ported (reason given)

## Claims: reading

| Feature (Cashflow 3) | Cashflow 4 |
|---|---|
| Own claims list with status (`/claims`, `api/claims/?user=`) | ✅ Overview |
| All viewable claims (`/admin/expenses`, `/admin/invoices`), visibility = `viewable_by` | ✅ "Alla utlägg" |
| Queues: attest, confirm, account, pay (`attestable_for` etc.) | ✅ Queue pages |
| Queue counts (`api/actions/`) | ✅ Sidebar badges |
| Queue overview by cost centre / owner (`api/actions/overview/`, `/admin`) | 🔜 4 (admin overview) |
| Search (fuzzy on description) | ✅ Substring on description, owner and `#number` |
| Filters: type, cost centre | ✅ |
| Filters: secondary cost centre, budget line, date range, owner, invoice number, verification, voucher series, reimbursement, attested/confirmed/paid/accounted/flagged checkboxes | 🔜 4 (advanced filter panel) |
| Sorting: date, total, description, owner, created | ✅ |
| Sorting: type, flagged, cost centre | ➖ queues keep flagged last automatically; type is a filter |
| Claim detail: parts, files, comments, confirmed by, payment, invoice fields | ✅ |
| Row context menu: open in new tab, copy link, view owner, account | ✅ real links (new tab, copy) · 🔜 4 view owner · 🔜 3 account |
| Profile pictures (rfinger, `api/users/profile-pictures/`) | 🔜 2 |

## Claims: writing

| Feature | Cashflow 4 |
|---|---|
| Create expense: description, date, parts (cost centre / secondary / budget line / amount), receipts (required) | 🔜 2 |
| Create invoice: description, invoice number, invoice date, due date, parts, files (required) | 🔜 2 |
| Part pickers from GOrdian (active + inactive names from existing parts) | 🔜 2 |
| Budget-line usage warning when a part would exceed the line's budget | 🔜 2 |
| HEIC/HEIF uploads converted to JPEG | 🔜 2 (in the browser) |
| PDF page count shown on upload (`RegisterPageCount`) | 🔜 2 |
| Edit own unpaid claim: fields, replace parts, add/remove files; editing parts or files voids the confirmation; editing unflags | 🔜 2 |
| Delete claim: owner or `delete` permission, not once paid | ✅ behind a confirmation dialog |
| Comment on a claim | ✅ Ctrl/⌘+Enter sends |
| Attest / unattest a part (scoped; never one's own expense; not while flagged) | ✅ |
| Confirm / unconfirm an expense's receipt (not while flagged) | ✅ |
| Confirm / unconfirm an invoice | ➖ the endpoints exist but the model always refuses (`NotConfirmableError`) |
| Flag / unflag an expense (attesters and payers) | ✅ |
| Pay an invoice (fully attested, unpaid) | ✅ |
| Pay out expenses: pending payouts per person with bank details, pick expenses, create a payment (`api/payments/`, `/admin/pay/expenses`) | ✅ Betala: one card per person; afterwards amount, account and reference to copy into the bank. Stricter: only ready, unflagged expenses |
| Payments list with search by tag (`/admin/payments`) | ✅ Utbetalningar |
| Workflow steps leave a comment ("Attesterar kvittodelen …", "Betalade ut i betalning N", …) | ✅ same Swedish texts, so both apps show the same history while they run side by side |

## New in Cashflow 4

| Feature | Why |
|---|---|
| "Next step" panel on every claim: where it stands, who acts next, the viewer's action, and why an expected action is unavailable | Nothing should be confusing |
| "Next in queue" (N) after opening a claim from a queue | Work through a queue without going back to the list |

## Notifications

| Feature | Cashflow 4 |
|---|---|
| Email the owner on every comment, including workflow comments, via spam (`/api/legacy/sendmail`) | ✅ through a Postgres outbox with retries; not for one's own comments |
| Other notification hooks (`on_attest`, `on_payment`, …) | ➖ never implemented in Cashflow 3 (`NotImplementedError`) |

## Accounting and Fortnox

| Feature | Cashflow 4 |
|---|---|
| Account a claim with an existing voucher number | 🔜 3 |
| Account via Fortnox: voucher rows, totals must match, duplicate checks (`AlreadyAccounted`, `CashflowVerificationMissing`, `FortnoxRecordMissing`) | 🔜 3 |
| Recommended accounts from GOrdian budget lines; credit accounts 2820 / 2440 | 🔜 3 |
| Fortnox OAuth connect / status / disconnect, token refresh (`refresh_fortnox_token`) | 🔜 3 |
| Fortnox accounts and cost centres lists (cached) | 🔜 3 |
| Voucher series list (Fortnox + seen in claims) and vouchers page (`/admin/vouchers`) | 🔜 3 |
| Feature flag `fortnox` (`api/features/`) | 🔜 3 |

## Budget, statistics and users

| Feature | Cashflow 4 |
|---|---|
| Budget page: cost centres from GOrdian, "blown" filter (`/budget`) | 🔜 4 |
| Cost centre detail: budget lines with uploaded / attested / paid vs budget (`/budget/[id]`) | 🔜 4 |
| GOrdian cache warm-up (`warm_gordian_cache`) | 🔜 2, in-process cache refreshed in the background |
| Statistics: monthly, yearly, leaderboard by total and count (`/stats`) | 🔜 4 |
| Personal stats on one's claims page (totals, rank) | 🔜 4 |
| Admin user page: a user's claims and bank details (`/admin/users/[user]`, pay or view-all) | 🔜 4 |
| User list (`api/users/`) | 🔜 4, as part of the admin user page |
| Own bank details | ✅ Profile |
| Language sv/en, dark mode | ✅ |
