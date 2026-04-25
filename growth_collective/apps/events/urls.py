from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('<int:event_id>/', views.event_detail, name='detail'),
    path('<int:event_id>/register/', views.register_event, name='register'),
    path('<int:event_id>/cancel/', views.cancel_registration, name='cancel'),
    path('my/', views.my_events, name='my_events'),
    path('feed/', views.event_feed, name='feed'),  # HTMX partial
]
