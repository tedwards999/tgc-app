from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.coaching_home, name='home'),
    path('book/', views.book_session, name='book'),
    path('confirm/', views.confirm_booking, name='confirm'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel'),
    path('coach/availability/', views.coach_availability, name='coach_availability'),
    path('coach/slots/', views.manage_slots, name='manage_slots'),
]
