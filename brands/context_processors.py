from .models import Brand
from products.models import ProductCategory, BrandProduct


def brand_context(request):
    """Add current brand information to template context"""
    # For now, we'll get the default brand
    # Later this can be enhanced to support subdomain-based brand detection
    try:
        brand = Brand.objects.get(is_default=True, is_active=True)
    except Brand.DoesNotExist:
        # Create default brand if none exists
        brand = Brand.objects.create(
            name="Model2Design",
            headline="Design and customize premium products with our advanced 3D modeling platform.",
            description="Create unique designs that stand out from the crowd.",
            is_default=True,
            is_active=True,
            primary_color="#007bff",
            secondary_color="#6c757d"
        )
    
    # Get product categories that have available products for this brand
    available_categories = ProductCategory.objects.filter(
        product__brandproduct__brand=brand,
        product__brandproduct__is_available=True,
        product__can_order=True
    ).distinct().order_by('name')
    
    return {
        'current_brand': brand,
        'brand_name': brand.name,
        'brand_styles': brand.get_brand_styles(),
        'brand_product_categories': available_categories,
    }