from django.shortcuts import render
from django.db import connection
from expenses import models

def index(request):
    return render(request, 'expenses/main.html')