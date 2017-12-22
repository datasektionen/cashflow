from django.shortcuts import render
from django.db import connection
from expenses import models
from django.db.models import Sum

"""
Simply renders main.html view.
"""
def index(request):
    return render(request, 'expenses/admin/index.html', {
    })