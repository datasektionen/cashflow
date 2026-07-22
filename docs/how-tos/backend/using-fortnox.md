# Using the Fortnox integration
We use the Fortnox API to account our expenses directly from Cashflow. This integration can be enabled or disabled your
`settings.py` by setting the `FORTNOX_ENABLED` variable to `True` or `False`. Note that the Fortnox integration expects
you to use a Fortnox service account and not per-user accounts. Permission checks are still performed using the
`PermissionProvider` (see [replacing the permission provider](./replace-permission-provider.md)).

## Required credentials

The following environment variables must be set when `FORTNOX_ENABLED` is `true`:

| Variable | Description |
|---|---|
| `FORTNOX_CLIENT_ID` | OAuth client ID from the Fortnox developer portal |
| `FORTNOX_CLIENT_SECRET` | OAuth client secret from the Fortnox developer portal |

## Optional configuration

These settings have defaults but can be overridden in `settings.py`:

| Setting | Default | Description |
|---|---|---|
| `FORTNOX_EXPENSE_VOUCHER_SERIES` | `"E"` | Voucher series used when accounting expenses |
| `FORTNOX_INVOICE_VOUCHER_SERIES` | `"U"` | Voucher series used when accounting invoices |
| `FORTNOX_EXPENSE_CREDIT_ACCOUNT` | `2820` | Credit account number for expense voucher rows |
| `FORTNOX_INVOICE_CREDIT_ACCOUNT` | `2440` | Credit account number for invoice voucher rows |
| `FORTNOX_ACCOUNT_CACHE_TIMEOUT` | `24` | Hours to cache accounts retrieved from Fortnox |
| `FORTNOX_COST_CENTER_CACHE_TIMEOUT` | `24` | Hours to cache cost centres retrieved from Fortnox |
| `FORTNOX_DESCRIPTION_FORMAT` | `"({id}) {description}"` | Format string for voucher descriptions. Available variables: `{id}`, `{description}`, `{kind}` |