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
| Queue overview by cost centre / owner (`api/actions/overview/`, `/admin`) | ✅ "Att göra" on the home page (`GetWorkOverview`); each count opens the queue filtered to it, pay counts open the person |
| Search (fuzzy on description) | ✅ Substring on description, owner and `#number` |
| Filters: type, cost centre | ✅ |
| Filters: secondary cost centre, budget line, date range, owner, invoice number, verification, voucher series, reimbursement, attested/confirmed/paid/accounted/flagged checkboxes | ✅ filter panel on every claims list (yes/no/any per status), active filters as removable chips, all in the URL. Voucher series on the vouchers page |
| Sorting: date, total, description, owner, created | ✅ |
| Sorting: type, flagged, cost centre | ➖ queues keep flagged last automatically; type is a filter |
| Claim detail: parts, files, comments, confirmed by, payment, invoice fields | ✅ |
| Row context menu: open in new tab, copy link, view owner, account | ✅ real links (new tab, copy) · ✅ view owner: owner names link to the person page for payers and admins · ✅ account: rows in the bookkeeping queue open the booking page |
| Profile pictures (rfinger, `api/users/profile-pictures/`) | ✅ cached 12 h on the server; one batched request per page (TanStack Pacer) |

## Claims: writing

| Feature | Cashflow 4 |
|---|---|
| Create expense: description, date, parts (cost centre / secondary / budget line / amount), receipts (required) | ✅ all problems shown at once, next to their fields |
| Create invoice: description, invoice number, invoice date, due date, parts, files (required) | ✅ |
| Part pickers from GOrdian (active + inactive names from existing parts) | ✅ narrowing step by step; an old name stays, marked "no longer in the budget" |
| Budget-line usage warning when a part would exceed the line's budget | ✅ also shows what is left, counting the claim's other parts |
| HEIC/HEIF uploads converted to JPEG | ✅ in the browser (heic-to, loaded only when needed) |
| PDF page count shown on upload (`RegisterPageCount`) | ✅ |
| Edit own unpaid claim: fields, replace parts, add/remove files; editing parts or files voids the confirmation; editing unflags | ✅ better: unchanged parts keep their attestations |
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
| Files upload while the form is filled in, with progress, retry and a camera button on phones | Submitting is instant; fewer lost receipts |
| Uploads are checked by content (JPEG, PNG, WebP, PDF) and served same-origin with a permission check | Cashflow 3 accepted any file and handed out presigned S3 links |
| GOrdian account ranges include their last account ("3021-3025") | Cashflow 3 dropped the last one |

## Notifications

| Feature | Cashflow 4 |
|---|---|
| Email the owner on every comment, including workflow comments, via spam (`/api/legacy/sendmail`) | ✅ through a Postgres outbox with retries; not for one's own comments |
| Other notification hooks (`on_attest`, `on_payment`, …) | ➖ never implemented in Cashflow 3 (`NotImplementedError`) |

## Accounting and Fortnox

| Feature | Cashflow 4 |
|---|---|
| Account a claim with an existing voucher number | ✅ with copyable text, date and amount for booking by hand; the number must look like `E123` |
| Account via Fortnox: voucher rows, totals must match, duplicate checks (`AlreadyAccounted`, `CashflowVerificationMissing`, `FortnoxRecordMissing`) | ✅ plus balanced debit/credit and known accounts and cost centres checked before Fortnox is called; an unrecorded voucher is reported with its number (`voucher_exists`) so it can be recorded instead of booked twice. The voucher lookup uses the series' sublist, not every voucher |
| Recommended accounts from GOrdian budget lines; credit accounts 2820 / 2440 | ✅ drafted on the server (`GetVoucherDraft`), rows for the same line merged; the credit row always balances the rest |
| Recommended Fortnox cost centre (exact name, or fuzzy "cost centre - secondary") | ✅ edit-distance similarity ≥ 0.9 instead of rapidfuzz |
| Fortnox OAuth connect / status / disconnect, token refresh (`refresh_fortnox_token`) | ✅ `/fortnox/auth`; refreshed in the background instead of by cron; a revoked access token is refreshed and retried, a refused refresh disconnects. "Connected" means a token row exists, not that the 1-hour access token is fresh (Cashflow 3 showed "disconnected" an hour after connecting) |
| Fortnox accounts and cost centres lists (cached) | ✅ 6 h in memory (Cashflow 3: accounts 24 h, cost centres 24 min) |
| Voucher series list (Fortnox + seen in claims) and vouchers page (`/admin/vouchers`) | ✅ `/vouchers`, searchable by voucher number, filtered by series |
| Feature flag `fortnox` (`api/features/`) | ✅ `GetMe.features.fortnox`, on when `FORTNOX_CLIENT_ID` is set |

## Budget, statistics and users

| Feature | Cashflow 4 |
|---|---|
| Budget page: cost centres from GOrdian, "blown" filter (`/budget`) | ✅ one page: cost centres grouped by kind with search, the overspent filter and a year switch; cost centres only seen on old claims are not listed |
| Cost centre detail: budget lines with uploaded / attested / paid vs budget (`/budget/[id]`) | ✅ beside the list (`/budget?cc=`), with a usage bar per line; each line links to its claims for the year |
| GOrdian cache warm-up (`warm_gordian_cache`) | ✅ in memory, loaded at start and refreshed every 12 hours |
| Statistics: monthly, yearly, leaderboard by total and count (`/stats`) | ✅ the year by month (expenses or invoices, sum or number), top ten by sum and by number for all time, this year or this month. Monthly is the yearly chart's month |
| Personal stats on one's claims page (totals, rank) | ✅ the place on this year's leaderboard on the home page; full stats on the person page. Equal totals share a place |
| Admin user page: a user's claims and bank details (`/admin/users/[user]`, pay or view-all) | ✅ `/users/$username` with bank details to copy, their stats and claims |
| User list (`api/users/`) | ✅ `/users`, searchable (50 at a time) |
| Own bank details | ✅ Profile |
| Language sv/en, dark mode | ✅ |
