from django.urls import path

from stats.api.views import (
    LeaderboardView,
    MonthlyStatisticsView,
    YearlyStatisticsView,
)

urlpatterns = [
    path("leaderboard/", LeaderboardView.as_view()),
    path("monthly/", MonthlyStatisticsView.as_view()),
    path("monthly/<int:year>/<int:month>/", MonthlyStatisticsView.as_view()),
    path("yearly/", YearlyStatisticsView.as_view()),
    path("yearly/<int:year>/", YearlyStatisticsView.as_view()),
]
