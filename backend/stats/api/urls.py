from django.urls import path

from stats.api.views import StatisticsView

urlpatterns = [
    path('leaderboard/', StatisticsView.as_view()),
]