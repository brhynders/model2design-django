from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.views.generic import ListView, DetailView
from .models import Product, ProductCategory, BrandProduct
from brands.mixins import BrandProductFilterMixin
from .data import products as PRODUCTS_DATA, bumpmap_textures as BUMPMAPS_DATA, fonts as FONTS_DATA, get_product_by_id


def product_list(request):
    # Get filter parameters
    selected_category = request.GET.get('category', '')
    create_template = request.GET.get('create_template') == '1'
    
    # Get current brand from middleware
    current_brand = getattr(request, 'brand', None)
    if not current_brand:
        from brands.models import Brand
        current_brand = Brand.get_by_subdomain()
    
    # Use static product data - show all products for all brands
    products = [p for p in PRODUCTS_DATA if p.get('canOrder', True)]
    
    # Filter by category if specified
    if selected_category:
        products = [p for p in products if selected_category in p.get('categories', [])]
    
    # Get category counts (with slugs for URL compatibility)
    from django.utils.text import slugify
    categories_with_counts = {}
    for product in PRODUCTS_DATA:
        if product.get('canOrder', True):
            for category in product.get('categories', []):
                if category not in categories_with_counts:
                    categories_with_counts[category] = {
                        'name': category, 
                        'slug': slugify(category),
                        'count': 0
                    }
                categories_with_counts[category]['count'] += 1
    
    category_counts = sorted(categories_with_counts.values(), key=lambda x: x['name'])
    
    # Get total product count
    total_product_count = len([p for p in PRODUCTS_DATA if p.get('canOrder', True)])
    
    context = {
        'products': products,
        'selected_category': selected_category,
        'create_template': create_template,
        'category_counts': category_counts,
        'total_product_count': total_product_count,
        'current_brand': current_brand,
    }
    
    return render(request, 'products/list.html', context)


def product_list_by_category(request, category_slug):
    # Find category from static data
    from django.utils.text import slugify
    category_name = None
    for product in PRODUCTS_DATA:
        for cat in product.get('categories', []):
            if slugify(cat) == category_slug:
                category_name = cat
                break
        if category_name:
            break
    
    if not category_name:
        from django.http import Http404
        raise Http404("Category not found")
    
    create_template = request.GET.get('create_template') == '1'
    
    # Get current brand from middleware
    current_brand = getattr(request, 'brand', None)
    if not current_brand:
        from brands.models import Brand
        current_brand = Brand.get_by_subdomain()
    
    # Filter products by category
    products = [p for p in PRODUCTS_DATA if p.get('canOrder', True) and category_name in p.get('categories', [])]
    
    # Get category counts (reuse logic from product_list)
    categories_with_counts = {}
    for product in PRODUCTS_DATA:
        if product.get('canOrder', True):
            for category in product.get('categories', []):
                if category not in categories_with_counts:
                    categories_with_counts[category] = {
                        'name': category, 
                        'slug': slugify(category),
                        'count': 0
                    }
                categories_with_counts[category]['count'] += 1
    
    category_counts = sorted(categories_with_counts.values(), key=lambda x: x['name'])
    
    # Get total product count
    total_product_count = len([p for p in PRODUCTS_DATA if p.get('canOrder', True)])
    
    context = {
        'products': products,
        'selected_category': category_name,
        'selected_category_obj': {'name': category_name, 'slug': category_slug},
        'create_template': create_template,
        'category_counts': category_counts,
        'total_product_count': total_product_count,
        'current_brand': current_brand,
    }
    
    return render(request, 'products/list.html', context)


def product_detail(request, pk):
    # Get current brand from middleware
    current_brand = getattr(request, 'brand', None)
    if not current_brand:
        from brands.models import Brand
        current_brand = Brand.get_by_subdomain()
    
    # Find product in static data
    product = get_product_by_id(int(pk))
    
    if not product or not product.get('canOrder', True):
        from django.http import Http404
        raise Http404("Product not found")
    
    context = {
        'product': product,
        'current_brand': current_brand,
    }
    
    return render(request, 'products/detail.html', context)
