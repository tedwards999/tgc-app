from django.contrib import admin
from .models import Coach, AvailabilitySlot, Booking, MonthlyUsage


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'experience_years', 'session_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'specialty']
    raw_id_fields = ['user']


@admin.register(AvailabilitySlot)
class AvailabilitySlotAdmin(admin.ModelAdmin):
    list_display = ['coach', 'time_range', 'status']
    list_filter = ['status', 'coach']
    raw_id_fields = ['coach']


class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'coach', 'scheduled_at', 'status', 'meeting_link']
    list_filter = ['status', 'coach']
    search_fields = ['user__email', 'coach__user__email']
    raw_id_fields = ['user', 'coach', 'slot']
    readonly_fields = ['created_at']
    actions = ['cancel_bookings']

    @admin.action(description='Cancel selected bookings')
    def cancel_bookings(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f'Cancelled {queryset.count()} bookings.')


admin.site.register(Booking, BookingAdmin)


@admin.register(MonthlyUsage)
class MonthlyUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'year', 'month', 'sessions_used']
    list_filter = ['year', 'month']
    search_fields = ['user__email']
