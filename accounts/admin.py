from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'name', 'phone', 'is_brand_owner', 'email_verified', 'is_staff', 'date_joined']
    list_filter = ['is_brand_owner', 'email_verified', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'name', 'phone']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('name', 'phone', 'is_brand_owner', 'email_verified')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('name', 'phone', 'is_brand_owner', 'email_verified')
        }),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'used', 'created_at']
    list_filter = ['used', 'created_at']
    search_fields = ['user__username', 'user__email', 'token']
    readonly_fields = ['token', 'created_at']
    autocomplete_fields = ['user']
