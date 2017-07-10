from django.shortcuts import render
from expenses import models


def user(request, username):
    # TODO: Add permissions
    return render(request, 'expenses/user.html',
                  {
                      "showuser": models.User.objects.get_by_natural_key(username)
                  })
