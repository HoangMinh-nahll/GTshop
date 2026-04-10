from django.urls import path
from .stats_views import stats_dashboard

urlpatterns = [
    path('', stats_dashboard, name='stats_dashboard'),
]