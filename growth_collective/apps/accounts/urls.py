from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('account/', views.account_settings, name='account_settings'),
    path('members/', views.member_directory, name='directory'),
    path('members/<int:user_id>/message/', views.start_dm, name='start_dm'),
    path('messages/', views.dm_inbox, name='dm_inbox'),
]
