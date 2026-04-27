from django.contrib import admin
from .models import Room, Message


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'requires_premium', 'is_active', 'created_at']
    list_filter = ['room_type', 'requires_premium', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'body_preview', 'is_deleted', 'created_at']
    list_filter = ['room', 'is_deleted']
    search_fields = ['sender__email', 'body']
    readonly_fields = ['sender', 'room', 'body', 'created_at']

    def body_preview(self, obj):
        return obj.body[:60]
    body_preview.short_description = 'Message'
