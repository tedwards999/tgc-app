from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'subscription_type', 'subscription_status', 'is_active', 'date_joined']
    list_filter = ['role', 'subscription_type', 'subscription_status', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login', 'referral_token']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Role & Subscription', {'fields': ('role', 'subscription_type', 'subscription_status')}),
        ('Referrals', {'fields': ('referral_token', 'referred_by')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )

    actions = ['suspend_users', 'reactivate_users', 'downgrade_to_free']

    @admin.display(description='Name')
    def full_name(self, obj):
        return obj.full_name

    @admin.action(description='Suspend selected users')
    def suspend_users(self, request, queryset):
        queryset.update(subscription_status='suspended')
        self.message_user(request, f'Suspended {queryset.count()} users.')

    @admin.action(description='Reactivate selected users')
    def reactivate_users(self, request, queryset):
        queryset.update(subscription_status='active')
        self.message_user(request, f'Reactivated {queryset.count()} users.')

    @admin.action(description='Downgrade selected users to free tier')
    def downgrade_to_free(self, request, queryset):
        queryset.update(subscription_type='free', subscription_status='cancelled')
        self.message_user(request, f'Downgraded {queryset.count()} users to free.')
