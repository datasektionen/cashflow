from django import template
from django.conf import settings

register = template.Library()
from expenses.models import *

@register.assignment_tag(takes_context=True)
def counts(context):
    user = context['request'].user
    context['counts'] = {
        'attest': Expense.view_attestable(user.profile.may_view_attest(), user).count() + Invoice.view_attestable(user.profile.may_view_attest(), user).count(),
        'confirm': Expense.confirmable().count() + 0,
        'pay': Expense.payable().count() + Invoice.payable().count(),
        'account': Expense.view_accountable(user.profile.may_view_account()).count() + Invoice.view_accountable(user.profile.may_view_account()).count()
    }

    return ''
