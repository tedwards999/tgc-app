from django.contrib import admin
from .models import Plan, Subscription, Payment, WebhookEvent


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_monthly', 'currency', 'subscription_type', 'is_active', 'is_popular']
    list_filter = ['is_active', 'currency']
    search_fields = ['name']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_end', 'cancel_at_period_end', 'created_at']
    list_filter = ['status', 'plan']
    search_fields = ['user__email', 'provider_subscription_id']
    raw_id_fields = ['user', 'plan']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'currency', 'status', 'description', 'created_at']
    list_filter = ['status', 'currency']
    search_fields = ['user__email', 'provider_payment_id']
    raw_id_fields = ['user', 'subscription']
    readonly_fields = ['created_at']


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'event_id', 'provider', 'processed', 'received_at']
    list_filter = ['event_type', 'processed', 'provider']
    search_fields = ['event_id', 'event_type']
    readonly_fields = ['event_id', 'event_type', 'provider', 'payload', 'received_at']
