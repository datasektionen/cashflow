from django import template
from django.conf import settings

register = template.Library()
from expenses.models import *
from invoices.models import Invoice


@register.simple_tag(takes_context=True)
def counts(context):
    user = context["request"].user
    context["counts"] = {
        "attest": Expense.objects.attestable_for(user).count()
        + Invoice.objects.attestable_for(user).count(),
        "confirm": Expense.confirmable().count() + 0,
        "pay": Expense.payable().count() + Invoice.payable().count(),
        "account": Expense.objects.accountable_for(user).count()
        + Invoice.objects.accountable_for(user).count(),
    }

    return ""
