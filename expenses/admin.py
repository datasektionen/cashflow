from django.contrib import admin
from expenses.models import *

# Our registered models
admin.site.register(BankAccount)
admin.site.register(Profile)
admin.site.register(Payment)
admin.site.register(Expense)
admin.site.register(File)
admin.site.register(ExpensePart)
admin.site.register(Comment)
