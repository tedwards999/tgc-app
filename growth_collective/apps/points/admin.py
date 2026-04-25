from django.contrib import admin
from .models import PointsLedger, UserRanking


@admin.register(PointsLedger)
class PointsLedgerAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'points', 'description', 'created_at']
    list_filter = ['action_type']
    search_fields = ['user__email', 'action_type', 'description']
    readonly_fields = ['created_at']
    raw_id_fields = ['user']

    def has_change_permission(self, request, obj=None):
        return False  # Ledger is append-only


@admin.register(UserRanking)
class UserRankingAdmin(admin.ModelAdmin):
    list_display = ['user', 'tier', 'total_points', 'monthly_points', 'updated_at']
    list_filter = ['tier']
    search_fields = ['user__email']
    readonly_fields = ['updated_at']
    raw_id_fields = ['user']
    ordering = ['-total_points']
