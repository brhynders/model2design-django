from django.contrib import admin
from .models import Design, DesignTemplate, DesignShare


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'brand', 'product', 'public', 'created_at', 'updated_at']
    list_filter = ['public', 'brand', 'created_at', 'updated_at']
    search_fields = ['name', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-updated_at']


@admin.register(DesignTemplate)
class DesignTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'product', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active', 'brand', 'created_at']
    search_fields = ['name', 'description', 'brand__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['sort_order', '-created_at']


@admin.register(DesignShare)
class DesignShareAdmin(admin.ModelAdmin):
    list_display = ['design', 'share_code', 'views', 'created_at']
    list_filter = ['created_at']
    search_fields = ['design__name', 'share_code']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
