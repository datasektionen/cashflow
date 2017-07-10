from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse


def index(request):
    return render(request, 'main.html')


def login(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('https://login2.datasektionen.se/login?callback=' + reverse('expenses-api-login'))
    else:
        return HttpResponseRedirect(reverse('expenses-index'))
