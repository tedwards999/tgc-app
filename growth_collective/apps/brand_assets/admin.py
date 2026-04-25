from django.contrib import admin
from .models import BrandAsset


@admin.register(BrandAsset)
class BrandAssetAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'access_level', 'download_count', 'is_active', 'created_at']
    list_filter = ['category', 'access_level', 'is_active']
    search_fields = ['title', 'description']
    readonly_fields = ['download_count', 'created_at', 'updated_at']
    list_editable = ['is_active']

    fieldsets = [
        (None, {'fields': ['title', 'description', 'category', 'access_level']}),
        ('Files', {'fields': ['file', 'preview_image', 'file_size_bytes']}),
        ('Stats', {'fields': ['download_count', 'is_active', 'created_at', 'updated_at']}),
    ]
