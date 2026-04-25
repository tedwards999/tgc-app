from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    path('', views.deal_board, name='board'),
    path('submit/', views.submit_referral, name='submit'),
    path('<int:referral_id>/engage/', views.engage_referral, name='engage'),
    path('<int:referral_id>/success/', views.mark_successful, name='mark_successful'),
]
