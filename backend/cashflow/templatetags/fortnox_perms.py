from django import template

from cashflow.utils import may_authenticate_fortnox as _may_authenticate_fortnox

register = template.Library()


@register.filter
def may_authenticate_fortnox(user):
    return _may_authenticate_fortnox(user)
