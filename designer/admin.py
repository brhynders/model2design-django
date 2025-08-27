from django.contrib import admin
from .models import Design, DesignTemplate, DesignShare, DesignImage


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


@admin.register(DesignImage)
class DesignImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_owner', 'filetype', 'file_size', 'width', 'height', 'created_at']
    list_filter = ['filetype', 'created_at', 'updated_at']
    search_fields = ['name', 'user__email', 'session_id']
    readonly_fields = ['file_size', 'width', 'height', 'filetype', 'created_at', 'updated_at', 'thumbnail']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def get_owner(self, obj):
        """Display owner information (user or guest session)"""
        if obj.user:
            return f"User: {obj.user.email}"
        return f"Guest: {obj.session_id}"
    get_owner.short_description = 'Owner'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')
