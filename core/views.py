from django.shortcuts import render
from brands.models import Brand
from products.models import Product, ProductCategory, BrandProduct
from products.data import products as PRODUCTS_DATA


def home(request):
    """Homepage view with exact HTML from PHP"""
    # Get current brand from middleware
    current_brand = getattr(request, 'brand', None)
    if not current_brand:
        current_brand = Brand.get_by_subdomain()
    
    # Get products from static data
    brand_products = [p for p in PRODUCTS_DATA if p.get('canOrder', True)]
    
    # Organize products by category for dynamic tab display
    from django.utils.text import slugify
    products_by_category = {}
    category_info = []  # List of dicts with category info and products
    
    for product in brand_products:
        categories = product.get('categories', [])
        for category_name in categories:
            category_slug = slugify(category_name)
            
            if category_slug not in products_by_category:
                products_by_category[category_slug] = []
            products_by_category[category_slug].append(product)
    
    # Create category_info with products included
    for slug, products in products_by_category.items():
        # Get category name from first product
        if products:
            category_name = products[0].get('categories', [])[0] if products[0].get('categories') else slug
            category_info.append({
                'name': category_name,
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
        'all_products_count': len(brand_products),
        'category_info': category_info,
    }
    
    return render(request, 'home.html', context)
