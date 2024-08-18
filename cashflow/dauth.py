import json
import re
import urllib.parse

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect


class DAuth(object):
    """
    Authenticates user through the login API.
    """

    @staticmethod
    def authenticate(token=None):
        """
        Do the authentication via the login system.
        Save user in database if did not exist before.
        """
        url = settings.LOGIN_API_URL + '/verify/' + str(token) + '.json?api_key=' + settings.LOGIN_API_KEY

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
            return user
        else:
            print("Response from login:", req)

    @staticmethod
    def get_user(user_id):
        """
        Get user from kth user id.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def get_permissions(user):
    """
    Get permissions for user through the pls API.
    """

    # Jag bryr mig inte om regler och om jag vill lägga saker i en godtycklig dict så gör jag det.

    if 'cached_permissions' not in user.__dict__:
        # Fetch permissions from pls and store timestamp
        response = requests.get(settings.PLS_URL + '/api/user/' + user.username + '/cashflow/')
        user.__dict__['cached_permissions'] = json.loads(urllib.parse.unquote(response.content.decode('utf-8')))

    return user.__dict__['cached_permissions']

def has_permission(permission, request):
    """
    Check is user has permission to specific property.
    Gets user from request.
    """

    return permission in get_permissions(request.user)


class AuthRequiredMiddleware(object):

    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        """
        Middleware for defining authentication.
        Forces user to be authenticated before sending on.
        """
        path = request.META['PATH_INFO']
        whitelist = ['^/$', '^/login/$', '^/login/.*$', "^/budget/.*$"]

        for regex in whitelist:
            pattern = re.compile(regex)
            if pattern.match(path):
                return None
        if not request.user.is_authenticated():
            return HttpResponseRedirect("/")
        return None
