from django.db.models import Q
from .models import Brand
from products.models import BrandProduct


class BrandFilterMixin:
    """
    Mixin to automatically filter products based on current brand
    """
    
    def get_brand(self):
        """Get the current brand from request"""
        return getattr(self.request, 'brand', Brand.get_by_subdomain())
    
    def get_brand_products_queryset(self):
        """Get products available for the current brand"""
        from products.models import Product
        
        brand = self.get_brand()
        
        # Get products that are available for this brand
        brand_product_ids = BrandProduct.objects.filter(
            brand=brand,
            is_available=True
        ).values_list('product_id', flat=True)
        
        # If no brand-specific products exist, return empty queryset
        if not brand_product_ids.exists():
            return Product.objects.none()
        
        return Product.objects.filter(
            id__in=brand_product_ids,
            can_order=True
        )
    
    def get_context_data(self, **kwargs):
        """Add brand context to templates"""
        context = super().get_context_data(**kwargs)
        context['current_brand'] = self.get_brand()
        return context


class BrandProductFilterMixin(BrandFilterMixin):
    """
    Specific mixin for product list views
    """
    
    def get_queryset(self):
        """Override to return brand-filtered products"""
        queryset = super().get_queryset() if hasattr(super(), 'get_queryset') else None
        
        # If parent has queryset, filter it by brand
        if queryset is not None:
            brand = self.get_brand()
            brand_product_ids = BrandProduct.objects.filter(
                brand=brand,
                is_available=True
            ).values_list('product_id', flat=True)
            
            if brand_product_ids.exists():
                return queryset.filter(id__in=brand_product_ids)
            else:
                # For any brand with no products, return empty queryset
                return queryset.none()
        
        # If no parent queryset, return brand-filtered products
        return self.get_brand_products_queryset()
    
    def get_brand_pricing(self, product, quantity=1):
        """Get brand-specific pricing for a product"""
        brand = self.get_brand()
        
        try:
            brand_product = BrandProduct.objects.get(
                brand=brand,
                product=product,
                is_available=True
            )
            return brand_product.get_price(quantity)
        except BrandProduct.DoesNotExist:
            # Fall back to default product pricing
            return product.get_base_price()
    
    def get_context_data(self, **kwargs):
        """Add brand-specific context"""
        context = super().get_context_data(**kwargs)
        
        # Add brand pricing helper to context
        context['get_brand_pricing'] = self.get_brand_pricing
        
        return context