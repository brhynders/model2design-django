from django.contrib import admin
from .models import Product, ProductCategory, ProductImage, BrandProduct


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    ordering = ['name']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image_url', 'alt_text', 'is_primary']


class BrandProductInline(admin.TabularInline):
    model = BrandProduct
    extra = 1
    fields = ['brand', 'is_available', 'custom_prices']
    autocomplete_fields = ['brand']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_categories', 'can_order', 'get_base_price', 'created_at']
    list_filter = ['can_order', 'categories', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['categories']
    inlines = [ProductImageInline, BrandProductInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'categories')
        }),
        ('3D Model & Display', {
            'fields': ('model_link', 'thumbnail', 'initial_layer', 'initial_bumpmap')
        }),
        ('Product Details', {
            'fields': ('sizes', 'prices', 'supported_bumpmaps', 'product_details', 'mesh_settings')
        }),
        ('Availability', {
            'fields': ('can_order',)
        }),
    )
    
    def get_categories(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()])
    get_categories.short_description = 'Categories'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    autocomplete_fields = ['product']


@admin.register(BrandProduct)
class BrandProductAdmin(admin.ModelAdmin):
    list_display = ['brand', 'product', 'is_available', 'has_custom_prices', 'created_at']
    list_filter = ['brand', 'is_available', 'created_at']
    search_fields = ['brand__name', 'product__name']
    autocomplete_fields = ['brand', 'product']
    
    def has_custom_prices(self, obj):
        return bool(obj.custom_prices)
    has_custom_prices.boolean = True
    has_custom_prices.short_description = 'Custom Pricing'
