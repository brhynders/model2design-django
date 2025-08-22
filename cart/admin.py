from django.contrib import admin
from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'total_items', 'subtotal', 'total', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['total_items', 'subtotal', 'shipping_cost', 'total', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'cart', 'design_id', 'product_id', 'quantity', 'price', 'total_price', 'created_at']
    list_filter = ['created_at', 'product_id']
    search_fields = ['design_name', 'design_id', 'cart__user__email']
    readonly_fields = ['total_price', 'is_guest_design', 'sizes_display', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Design Information', {
            'fields': ('cart', 'design_id', 'design_name', 'thumbnail', 'product_id')
        }),
        ('Quantity & Pricing', {
            'fields': ('sizes', 'quantity', 'price', 'total_price')
        }),
        ('Status', {
            'fields': ('is_guest_design', 'sizes_display', 'created_at', 'updated_at')
        })
    )