from django.contrib import admin
from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'recipient_email', 'subject', 'status', 'sent_at']
    list_filter = ['status', 'template_name']
    search_fields = ['recipient_email', 'subject']
    readonly_fields = ['user', 'recipient_email', 'subject', 'template_name', 'status', 'error_message', 'sent_at']
    raw_id_fields = ['user']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
