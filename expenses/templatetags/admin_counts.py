from django import template
from django.conf import settings

register = template.Library()
from expenses.models import *

@register.assignment_tag(takes_context=True)
def counts(context):
    user = context['request'].user
    context['counts'] = {
        'attest': Expense.view_attestable(user).count() + Invoice.view_attestable(user).count(),
        'confirm': Expense.confirmable().count() + 0,
        'pay': Expense.payable().count() + Invoice.payable().count(),
        'account': Expense.view_accountable(user).count() + Invoice.view_accountable(user).count()
    }

    return ''
