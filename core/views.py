from django.shortcuts import render
from brands.models import Brand
from products.models import Product, ProductCategory, BrandProduct


def home(request):
    """Homepage view with exact HTML from PHP"""
    # Get current brand from middleware
    current_brand = getattr(request, 'brand', None)
    if not current_brand:
        current_brand = Brand.get_by_subdomain()
    
    # Get brand-filtered products (same logic as products/views.py)
    brand_product_ids = BrandProduct.objects.filter(
        brand=current_brand,
        is_available=True
    ).values_list('product_id', flat=True)
    
    # Get products for this brand
    if brand_product_ids.exists():
        brand_products = Product.objects.filter(
            id__in=brand_product_ids,
            can_order=True
        ).prefetch_related('categories')
    else:
        # If brand has no products assigned, show empty list
        brand_products = Product.objects.none()
    
    # Organize products by category for dynamic tab display
    products_by_category = {}
    category_info = []  # List of dicts with category info and products
    
    for product in brand_products:
        categories = product.categories.all()
        for category in categories:
            category_name = category.name
            category_slug = category.name.lower().replace(' ', '-')
            
            if category_slug not in products_by_category:
                products_by_category[category_slug] = []
            products_by_category[category_slug].append(product)
    
    # Create category_info with products included
    for slug, products in products_by_category.items():
        # Get category name from first product
        if products:
            category_name = products[0].categories.filter(name__icontains=slug.replace('-', ' ')).first()
            if category_name:
                category_info.append({
                    'name': category_name.name,
                    'slug': slug,
                    'tab_id': slug.replace('-', '_'),  # For valid HTML IDs
                    'products': products
                })
    
    # Sort categories alphabetically
    category_info.sort(key=lambda x: x['name'])
    
    context = {
        'current_brand': current_brand,
        'brand_name': current_brand.name if current_brand else 'Model2Design',
        'brand_products': brand_products[:8],  # Limit to 8 for homepage
        'all_products_count': brand_products.count(),
        'category_info': category_info,
    }
    
    return render(request, 'home.html', context)
