# Replace permission provider

The Computer Science Chapter uses our own permission service called Hive. But you can replace this by subclassing
the `PermissionProvider` class (`core/permissions.py`). Our implementation `Hive` can be found in `cashflow/dauth.py`.

## 1. Create your own permission provider

Create a subclass of `PermissionProvider` This class expects methods to check if a user has permission to perform an
action on a given expense or invoice, as well
as providing Django querysets for all expenses and invoices a user can perform an action on. You need to implement
all methods for everything to work as expected.

## 2. Configure the permission provider

In your `settings.py` file, set the `PERMISSION_PROVIDER` variable to the path of your permission provider class. For
example:

```python
PERMISSION_PROVIDER = 'myapp.permissions.MyPermissionProvider'
```
