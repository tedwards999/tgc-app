from django.contrib import admin
from .models import Event, EventAttendee


class EventAttendeeInline(admin.TabularInline):
    model = EventAttendee
    extra = 0
    raw_id_fields = ['user']
    readonly_fields = ['registered_at']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'access_level', 'datetime', 'attendee_count', 'is_published']
    list_filter = ['event_type', 'access_level', 'is_published']
    search_fields = ['title', 'description']
    raw_id_fields = ['host']
    readonly_fields = ['created_at']
    inlines = [EventAttendeeInline]
    actions = ['send_reminders', 'cancel_event']

    @admin.display(description='Attendees')
    def attendee_count(self, obj):
        return obj.attendee_count

    @admin.action(description='Send reminder to all attendees')
    def send_reminders(self, request, queryset):
        count = 0
        for event in queryset:
            count += event.attendees.filter(status='registered').count()
        self.message_user(request, f'Reminders queued for {count} attendees.')

    @admin.action(description='Cancel selected events')
    def cancel_event(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, f'Cancelled {queryset.count()} events.')
