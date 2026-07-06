from django import template

register = template.Library()


@register.filter
def pad_nbsp(value, width):
    s = str(value)
    pad = max(0, int(width) - len(s))
    return s + " " * pad
