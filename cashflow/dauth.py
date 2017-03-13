import requests
import json
from django.conf import settings
from django.contrib.auth.models import User
from expenses.models import Person


class dAuth(object):

    def authenticate(self, token=None):

        url = 'http://login2.datasektionen.se/verify/' + token + '.json?api_key=' + settings.AUTH_API_KEY
        req = requests.get(url)
        if req.status_code == 200:
            data = req.json()

            try:
                user = User.objects.get(username=data["user"])
            except User.DoesNotExist:
                user = User(first_name=data["first_name"],last_name=data["last_name"],username=data["user"],email=data["emails"])
                user.save()
                p = Person(user=user)
                p.save()
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def has_permission(permission, user):
    permission_response = requests.get('http://pls.datasektionen.se/api/user/' + user.username + '/cashflow/' + permission + '/')
    return permission_response.json()