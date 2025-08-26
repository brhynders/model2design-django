from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Brand, BrandOwner, BrandImage, BrandImageCategory, 
    BrandTemplate, BrandEarnings, PartnerRequest, BrandBackground
)
from products.models import BrandProduct


class BrandProductInline(admin.TabularInline):
    model = BrandProduct
    extra = 1
    fields = ['product', 'is_available', 'custom_prices']
    autocomplete_fields = ['product']


class BrandOwnerInline(admin.TabularInline):
    model = BrandOwner
    extra = 0
    readonly_fields = ['created_at']


class BrandImageInline(admin.TabularInline):
    model = BrandImage
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['name', 'category', 'image_url', 'thumbnail_url', 'is_public']


class BrandTemplateInline(admin.TabularInline):
    model = BrandTemplate
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    fields = ['name', 'description', 'is_public', 'is_featured', 'usage_count']


class BrandBackgroundInline(admin.TabularInline):
    model = BrandBackground
    extra = 0
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    fields = ['name', 'image', 'thumbnail', 'is_active', 'is_default', 'sort_order', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'subdomain', 'is_default', 'is_active', 'get_product_count', 'created_at']
    list_filter = ['is_default', 'is_active', 'created_at']
    search_fields = ['name', 'slug', 'subdomain', 'contact_email']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'subdomain', 'description', 'is_default', 'is_active')
        }),
        ('Customization', {
            'fields': ('logo_url', 'primary_color', 'secondary_color')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'website_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [BrandOwnerInline, BrandProductInline, BrandImageInline, BrandTemplateInline, BrandBackgroundInline]
    
    def get_product_count(self, obj):
        return BrandProduct.objects.filter(brand=obj, is_available=True).count()
    get_product_count.short_description = 'Available Products'
    
    def get_readonly_fields(self, request, obj=None):
        readonly = ['created_at', 'updated_at']
        # Make subdomain readonly after creation to prevent breaking URLs
        if obj and obj.pk:
            readonly.append('subdomain')
        return readonly


@admin.register(BrandOwner)
class BrandOwnerAdmin(admin.ModelAdmin):
    list_display = ['user', 'brand', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at', 'brand']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'brand__name']
    readonly_fields = ['created_at']


@admin.register(BrandImageCategory)
class BrandImageCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'slug', 'created_at']
    list_filter = ['brand', 'created_at']
    search_fields = ['name', 'brand__name']
    readonly_fields = ['created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BrandImage)
class BrandImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'category', 'is_public', 'image_preview', 'created_at']
    list_filter = ['brand', 'category', 'is_public', 'created_at']
    search_fields = ['name', 'brand__name', 'alt_text']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand', 'category', 'alt_text', 'is_public')
        }),
        ('Images', {
            'fields': ('image_url', 'thumbnail_url', 'image_preview')
        }),
        ('Metadata', {
            'fields': ('file_size', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_preview(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.thumbnail_url)
        elif obj.image_url:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.image_url)
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(BrandTemplate)
class BrandTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'is_public', 'is_featured', 'usage_count', 'created_by', 'created_at']
    list_filter = ['brand', 'is_public', 'is_featured', 'created_at']
    search_fields = ['name', 'brand__name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'usage_count', 'thumbnail_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand', 'description', 'created_by')
        }),
        ('Settings', {
            'fields': ('is_public', 'is_featured', 'usage_count')
        }),
        ('Template Data', {
            'fields': ('template_data', 'thumbnail_url', 'thumbnail_preview'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.thumbnail_url)
        return "No thumbnail"
    thumbnail_preview.short_description = "Thumbnail"


@admin.register(BrandEarnings)
class BrandEarningsAdmin(admin.ModelAdmin):
    list_display = ['brand', 'order_id', 'amount', 'commission_amount', 'payment_status', 'transaction_date']
    list_filter = ['brand', 'payment_status', 'transaction_date']
    search_fields = ['brand__name', 'order_id', 'notes']
    readonly_fields = ['created_at', 'commission_amount']
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('brand', 'order_id', 'amount', 'transaction_date')
        }),
        ('Commission', {
            'fields': ('commission_rate', 'commission_amount')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_date', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(PartnerRequest)
class PartnerRequestAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'contact_name', 'email', 'status', 'created_at']
    list_filter = ['status', 'business_type', 'expected_volume', 'created_at']
    search_fields = ['business_name', 'contact_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Business Information', {
            'fields': ('business_name', 'website', 'business_type', 'expected_volume')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'email', 'phone')
        }),
        ('Social Media', {
            'fields': ('facebook', 'instagram', 'twitter', 'linkedin'),
            'classes': ('collapse',)
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status & Admin', {
            'fields': ('status', 'admin_notes', 'approved_brand', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Make all fields readonly except status and admin fields
        if obj:
            return ['business_name', 'website', 'business_type', 'expected_volume',
                   'contact_name', 'email', 'phone', 'facebook', 'instagram', 
                   'twitter', 'linkedin', 'message', 'created_at', 'updated_at']
        return ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        # Auto-set reviewed_by and reviewed_at when status changes
        if change and 'status' in form.changed_data:
            if obj.status != 'pending':
                obj.reviewed_by = request.user
                obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(BrandBackground)
class BrandBackgroundAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'is_active', 'is_default', 'sort_order', 'image_preview', 'created_at']
    list_filter = ['brand', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'brand__name']
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    list_editable = ['sort_order', 'is_active', 'is_default']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand', 'is_active', 'is_default', 'sort_order')
        }),
        ('Images', {
            'fields': ('image', 'thumbnail', 'image_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = "Preview"
