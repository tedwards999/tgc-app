from django.urls import path
from apps.chat import views

app_name = 'chat'

urlpatterns = [
    path('<slug:room_slug>/', views.room_detail, name='room'),
]
