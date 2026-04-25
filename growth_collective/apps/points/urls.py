from django.urls import path
from . import views

app_name = 'points'

urlpatterns = [
    path('', views.my_points, name='my_points'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
