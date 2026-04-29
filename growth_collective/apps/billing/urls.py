from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.billing_dashboard, name='dashboard'),
    path('pricing/', views.pricing, name='pricing'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('cancel/', views.cancel_subscription, name='cancel'),
    path('stripe/return/', views.stripe_return, name='stripe_return'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]
