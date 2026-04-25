from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.billing_dashboard, name='dashboard'),
    path('pricing/', views.pricing, name='pricing'),
    path('subscribe/<int:plan_id>/', views.subscribe, name='subscribe'),
    path('return/', views.subscription_return, name='return'),
    path('cancel/', views.cancel_subscription, name='cancel'),
    path('paypal/webhook/', views.paypal_webhook, name='webhook'),
]
