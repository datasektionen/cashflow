import urllib2
import json
from django.conf import settings
from django.contrib.auth.models import User
from expenses.models import Person

class dAuth(object):

    def authenticate(self, token=None):

        url = 'http://login2.datasektionen.se/verify/' + token +'.json?api_key=' + settings.AUTH_API_KEY
        req = urllib2.urlopen(url)
        serialized_data = req.read()
        if req.getCode() == 200:
            data = json.loads(serialized_data)

            try:
                user = User.objects.get(username=data["user"])
            except User.DoesNotExist:
                user = User(first_name=u["first_name"],last_name=u["last_name"],username=u["user"],email=u["emails"])
                user.save()
                p = Person(user=user)
                p.save()
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

