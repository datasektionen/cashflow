from django.shortcuts import render, redirect


def index(request):
    if not request.user.is_authenticated:
        callback_url = request.scheme + '://' + request.get_host() + '/api/login/'
        url = 'http://login2.datasektionen.se/login?callback=' + callback_url
        return redirect(url)

    return render(request, 'index.html')
