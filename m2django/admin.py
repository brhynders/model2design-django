from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html


class Model2DesignAdminSite(AdminSite):
    site_title = 'Model2Design Admin'
    site_header = 'Model2Design Administration'
    index_title = 'Welcome to Model2Design Admin Panel'
    
    def index(self, request, extra_context=None):
        """
        Display the main admin index page with custom stats
        """
        extra_context = extra_context or {}
        
        # Add custom stats
        from brands.models import Brand
        from products.models import Product, BrandProduct
        from accounts.models import User
        
        extra_context.update({
            'custom_stats': {
                'total_brands': Brand.objects.filter(is_active=True).count(),
                'total_products': Product.objects.filter(can_order=True).count(),
                'total_users': User.objects.filter(is_active=True).count(),
                'brand_product_relationships': BrandProduct.objects.filter(is_available=True).count(),
            }
        })
        
        return super().index(request, extra_context)


# Replace the default admin site
admin_site = Model2DesignAdminSite(name='admin')

# We need to register our models with the custom admin site
# This will be done automatically by Django's autodiscovery