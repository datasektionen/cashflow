from django.conf.urls import url, include

from budget import api_views

api_urlpatterns = [
    url(r'^latest.json$', api_views.latest_as_json)
]

urlpatterns = [
    url(r'^api/', include(api_urlpatterns), name='budget-api-latest'),
]
