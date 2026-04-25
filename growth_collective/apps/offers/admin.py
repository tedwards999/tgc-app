from django.contrib import admin
from .models import Offer, OfferEngagement


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider_name', 'submitted_by', 'category', 'is_active', 'is_featured', 'expires_at']
    list_filter = ['is_active', 'category', 'access_level', 'is_featured']
    search_fields = ['title', 'provider_name', 'short_description']
    readonly_fields = ['submitted_by', 'created_at', 'updated_at']
    list_editable = ['is_featured', 'is_active']

    fieldsets = [
        (None, {'fields': ['title', 'provider_name', 'provider_logo', 'category', 'access_level', 'submitted_by']}),
        ('Content', {'fields': ['short_description', 'full_description', 'discount_headline']}),
        ('Redemption', {'fields': ['redemption_url', 'redemption_code', 'redemption_instructions']}),
        ('Settings', {'fields': ['is_featured', 'is_active', 'expires_at', 'created_at', 'updated_at']}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('submitted_by')


@admin.register(OfferEngagement)
class OfferEngagementAdmin(admin.ModelAdmin):
    list_display = ['offer', 'user', 'created_at']
    search_fields = ['offer__title', 'user__email']
    raw_id_fields = ['offer', 'user']
    readonly_fields = ['created_at']
