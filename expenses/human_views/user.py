from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.urls import reverse

from cashflow.dauth import has_permission
from expenses import models
from expenses.forms import UserForm


def get_user(request, username):
    # TODO: Add permissions
    try:
        user = models.User.objects.get_by_natural_key(username)
        if not may_view_user(request, user):
            return HttpResponseForbidden()
        return render(request, 'expenses/user.html',
                      {
                          "showuser": user
                      })
    except ObjectDoesNotExist:
        raise Http404("Användaren finns inte")


def edit_user(request, username):
    try:
        user = models.User.objects.get_by_natural_key(username)
        if not may_view_user(request, user):
            return HttpResponseForbidden()
        if request.method == 'POST':
            received_form = UserForm(request.POST, instance=user.profile)
            if received_form.is_valid():
                received_form.save()
                return HttpResponseRedirect(reverse('expenses-user', args=[username]))
        else:

            form = UserForm(instance=user.profile)
            return render(request, 'expenses/edit_user.html', {
                "form": form
            })
    except ObjectDoesNotExist:
        raise Http404("Användaren finns inte")


def may_view_user(request, user_to_view):
    return (request.user == user_to_view) or has_permission('admin', request)
