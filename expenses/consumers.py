# coding=utf-8
from channels import Group
from channels.sessions import channel_session

from expenses.models import Expense
from expenses.api_views.expense import may_view_expense


@channel_session
def ws_connect(message):
    group = message['path'].strip('/')
    if group.split('/')[0] is 'expense':
        if may_view_expense(Expense.objects.get(id=int(group.split('/')[1])), message.http_session):
            Group('cashflow-' + group).add(message.reply_channel)
            message.channel_session['group'] = group
    else:
        if has_permission(group, message.http_session):
            group = group.replace('*', '.').replace(u'å', 'a').replace(u'ä', 'a').replace(u'ö', 'o')
            Group('cashflow-' + group).add(message.reply_channel)
            message.channel_session['group'] = group


@channel_session
def ws_disconnect(message):
    group = message.channel_session['group']
    Group('chat-' + group).discard(message.reply_channel)


def has_permission(permission, http_session):
    return permission in http_session['permissions']
