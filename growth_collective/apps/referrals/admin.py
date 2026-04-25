from django.contrib import admin
from .models import Referral, ReferralEngagement, MonthlyReferralPrompt, MonthlyPromptCompletion


class ReferralEngagementInline(admin.TabularInline):
    model = ReferralEngagement
    extra = 0
    raw_id_fields = ['user']
    readonly_fields = ['created_at']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['title', 'referrer', 'referral_type', 'status', 'is_published', 'created_at']
    list_filter = ['referral_type', 'status', 'is_published']
    search_fields = ['title', 'referrer__email', 'contact_name', 'contact_email']
    raw_id_fields = ['referrer', 'referred_user']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status', 'is_published']
    inlines = [ReferralEngagementInline]


@admin.register(MonthlyReferralPrompt)
class MonthlyReferralPromptAdmin(admin.ModelAdmin):
    list_display = ['month', 'is_active', 'prompt_text']
    list_editable = ['is_active']


@admin.register(MonthlyPromptCompletion)
class MonthlyPromptCompletionAdmin(admin.ModelAdmin):
    list_display = ['user', 'prompt', 'year', 'month', 'completed_at']
    list_filter = ['year', 'month']
    search_fields = ['user__email']
    raw_id_fields = ['user', 'prompt']
    readonly_fields = ['completed_at']
