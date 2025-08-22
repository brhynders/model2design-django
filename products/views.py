from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.views.generic import ListView, DetailView
from .models import Product, ProductCategory, BrandProduct
from brands.mixins import BrandProductFilterMixin


def product_list(request):
    # Get filter parameters
    selected_category = request.GET.get('category', '')
    create_template = request.GET.get('create_template') == '1'
    
    # Get current brand from middleware
    current_brand = getattr(request, 'brand', None)
    if not current_brand:
        from brands.models import Brand
        current_brand = Brand.get_by_subdomain()
    
    # Get brand-filtered products
    brand_product_ids = BrandProduct.objects.filter(
        brand=current_brand,
        is_available=True
    ).values_list('product_id', flat=True)
    
    # All brands (including default) only show their assigned products
    if brand_product_ids.exists():
        products = Product.objects.filter(
            id__in=brand_product_ids,
            can_order=True
        ).prefetch_related('categories')
    else:
        # If brand has no products assigned, show empty list
        products = Product.objects.none()
    
    # Filter by category if specified
    if selected_category:
        products = products.filter(categories__name=selected_category)
    
    # Get category counts for sidebar (only for available products)
    if brand_product_ids.exists():
        category_filter = Q(product__id__in=brand_product_ids, product__can_order=True)
    else:
        category_filter = Q(pk__isnull=True)  # Empty filter
        
    category_counts = ProductCategory.objects.annotate(
        count=Count('product', filter=category_filter)
    ).filter(count__gt=0).order_by('name')
    
    # Get total product count for this brand
    if brand_product_ids.exists():
        total_product_count = Product.objects.filter(
            id__in=brand_product_ids,
            can_order=True
        ).count() if not selected_category else products.count()
    else:
        total_product_count = 0
    
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
    # Get the category by slug
    category = get_object_or_404(ProductCategory, slug=category_slug)
    create_template = request.GET.get('create_template') == '1'
    
    # Get current brand from middleware
    current_brand = getattr(request, 'brand', None)
    if not current_brand:
        from brands.models import Brand
        current_brand = Brand.get_by_subdomain()
    
    # Get brand-filtered products
    brand_product_ids = BrandProduct.objects.filter(
        brand=current_brand,
        is_available=True
    ).values_list('product_id', flat=True)
    
    # All brands (including default) only show their assigned products
    if brand_product_ids.exists():
        products = Product.objects.filter(
            id__in=brand_product_ids,
            can_order=True, 
            categories=category
        ).prefetch_related('categories')
    else:
        # If brand has no products assigned, show empty list
        products = Product.objects.none()
    
    # Get category counts for sidebar (only for available products)
    if brand_product_ids.exists():
        category_filter = Q(product__id__in=brand_product_ids, product__can_order=True)
    else:
        category_filter = Q(pk__isnull=True)  # Empty filter
        
    category_counts = ProductCategory.objects.annotate(
        count=Count('product', filter=category_filter)
    ).filter(count__gt=0).order_by('name')
    
    # Get total product count for this brand
    if brand_product_ids.exists():
        total_product_count = Product.objects.filter(
            id__in=brand_product_ids,
            can_order=True
        ).count()
    else:
        total_product_count = 0
    
    context = {
        'products': products,
        'selected_category': category.name,
        'selected_category_obj': category,
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
    
    # Check if product is available for this brand
    product = get_object_or_404(Product, pk=pk, can_order=True)
    
    # Verify product is available for current brand (applies to all brands now)
    brand_product = BrandProduct.objects.filter(
        brand=current_brand,
        product=product,
        is_available=True
    ).first()
    
    if not brand_product:
        # Product not available for this brand
        from django.http import Http404
        raise Http404("Product not available for this brand")
    
    context = {
        'product': product,
        'current_brand': current_brand,
    }
    
    return render(request, 'products/detail.html', context)
