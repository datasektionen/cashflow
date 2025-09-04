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
    Get permissions for user through the Hive API.

    Result is a dictionary { perm_id => scope[] | True }
    """

    # Jag bryr mig inte om regler och om jag vill lägga saker i en godtycklig dict så gör jag det.

    if 'cached_permissions' not in user.__dict__:
        # Fetch permissions from Hive
        response = requests.get(
            settings.HIVE_URL + '/api/v1/user/' + user.username,
            headers={"Authorization": "Bearer " + settings.HIVE_SECRET}
        )
        perms = json.loads(response.content.decode('utf-8'))

        if type(perms) != list:
            raise TypeError(f"Invalid response: {perms}")

        mapping = {}

        for perm in perms:
            perm_id, scope = perm["id"], perm["scope"]

            if scope is None or scope == "*":
                mapping[perm_id] = True
            elif perm_id not in mapping:
                mapping[perm_id] = [scope.lower()]
            elif mapping[perm_id] is not True:
                mapping[perm_id].append(scope.lower())
            # else: don't overwrite an existing True (do nothing)

        user.__dict__['cached_permissions'] = mapping

    return user.__dict__['cached_permissions']

def has_unscoped_permission(perm_id, user):
    """
    Check if user has a specific unscoped permission.
    """

    return get_permissions(user).get(perm_id) is True

def has_scoped_permission(perm_id, scope, user):
    """
    Check if user has a specific scoped permission.
    """

    scopes = get_permissions(user).get(perm_id) or []

    return scopes is True or scope.lower() in scopes

def has_any_permission_scope(perm_id, user):
    """
    Check if user has any scope for a specific permission.
    """

    return perm_id in get_permissions(user)


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
