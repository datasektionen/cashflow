from django import template
from django.conf import settings

register = template.Library()
from expenses.models import *

@register.assignment_tag(takes_context=True)
def counts(context):
    user = context['request'].user
    context['counts'] = {
        'attest': Expense.attestable(user.profile.may_attest(), user).count(),
        'confirm': Expense.confirmable().count(),
        'pay': Expense.payable().count(),
        'account': Expense.accountable(user.profile.may_account()).count()
    }

    return ''