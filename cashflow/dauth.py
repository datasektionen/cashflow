import re

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from expenses.models import Profile


class DAuth(object):

    @staticmethod
    def authenticate(token=None):

        url = 'http://login2.datasektionen.se/verify/' + str(token) + '.json?api_key=' + settings.AUTH_API_KEY
        req = requests.get(url)
        if req.status_code == 200:
            data = req.json()

            try:
                user = User.objects.get(username=data["user"])
            except User.DoesNotExist:
                user = User(
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    username=data["user"],
                    email=data["emails"]
                )
                user.save()
                p = Profile(user=user)
                p.save()
            return user

    @staticmethod
    def get_user(user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def get_permissions(user):
    return requests.get(
        'http://pls.datasektionen.se/api/user/' + user.username + '/cashflow/'
    ).json()


def has_permission(permission, request):
    if 'permissions' not in request.session:
        # Fetch permissions from pls and store timestamp
        request.session['permissions'] = requests.get(
                'http://pls.datasektionen.se/api/user/' + request.user.username + '/cashflow/'
            ).json()

    return permission in request.session['permissions']


class AuthRequiredMiddleware(object):
    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        path = request.META['PATH_INFO']
        whitelist = ['^/$', '^/login/$', '^/api/.*$']

        for regex in whitelist:
            pattern = re.compile(regex)
            if pattern.match(path):
                return None
        if not request.user.is_authenticated():
            return HttpResponseRedirect("/")
        return None
