from typing import *
import json

import requests
from django.conf import settings
from django.contrib.auth.models import User

from authlib.integrations.django_client import OAuth
from authlib.integrations.base_client.errors import OAuthError, MismatchingStateError


client = OAuth().register(
    name="sso",
    client_id=settings.OIDC_ID,
    client_secret=settings.OIDC_SECRET,
    server_metadata_url=f"{settings.OIDC_PROVIDER}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid profile email"}
)


class DAuth(object):
    """
    Authenticates user through the sso API.
    """

    @staticmethod
    def authenticate(request):
        """
        Do the authentication via the sso system.
        Save user in database if did not exist before.
        """
        
        try:
            token = client.authorize_access_token(request)
        except (OAuthError, MismatchingStateError) as error:
            # These errors are generated for various kinds of invalid codes.
            print(f"Authentication failed: {error}")
            return None
        
        user = client.userinfo(token=token)
        
        try:
            user = User.objects.get(username=user["sub"])
        except User.DoesNotExist:
            user = User(
                first_name=user["given_name"],
                last_name=user["family_name"],
                username=user["sub"],
                email=user["email"]
            )
            user.save()
        return user

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
            settings.HIVE_URL + '/api/v1/user/' + user.username + '/permissions',
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


