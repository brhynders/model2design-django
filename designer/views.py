from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
import json
import uuid
from .models import Design, DesignTemplate, DesignShare
from brands.models import Brand, BrandBackground
from products.models import Product
from products.data import products as PRODUCTS_DATA, bumpmap_textures as BUMPMAPS_DATA, fonts as FONTS_DATA, get_product_by_id


def designer_view(request):
    """Main designer interface view"""
    # Get current brand from middleware
    current_brand = request.brand
    
    # Check if user is a brand owner
    is_brand_owner = False
    if request.user.is_authenticated:
        is_brand_owner = request.user.is_brand_owner
    
    # Get product ID and design ID from URL
    product_id = request.GET.get('product', 0)
    design_id = request.GET.get('design')
    copy_design_id = request.GET.get('copy')
    template_id = request.GET.get('template')
    create_template = request.GET.get('create_template') == '1'
    template_edit_id = request.GET.get('template_edit')
    
    # Convert to int
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        product_id = 0
        
    # Find the current product from static data
    current_product = None
    if product_id is not None:
        current_product = get_product_by_id(product_id)
    
    # Fall back to first product if none specified or not found
    if not current_product and PRODUCTS_DATA:
        current_product = PRODUCTS_DATA[0]
        product_id = current_product['id']
    
    # Load design data if design ID is provided
    design_data = None
    if design_id and request.user.is_authenticated:
        try:
            design = Design.objects.get(id=design_id, user=request.user)
            design_data = {
                'id': design.id,
                'name': design.name,
                'product_id': design.product,
                'design_data': design.data,
                'screenshots': {
                    'front': design.thumbnail_front,
                    'back': design.thumbnail_back,
                    'left': design.thumbnail_left,
                    'right': design.thumbnail_right
                }
            }
        except Design.DoesNotExist:
            # Check session for guest designs
            if 'guest_designs' in request.session:
                for guest_design in request.session['guest_designs']:
                    if guest_design.get('id') == design_id:
                        design_data = {
                            'id': guest_design['id'],
                            'name': guest_design['name'],
                            'product_id': guest_design['product_id'],
                            'design_data': guest_design['design_data'],
                            'screenshots': guest_design.get('screenshots', {})
                        }
                        break
    
    # Handle copy design functionality
    if copy_design_id and request.user.is_authenticated:
        try:
            copy_design_id = int(copy_design_id)
            original_design = Design.objects.get(id=copy_design_id, public=True)
            
            # Create a duplicate design for the current user
            duplicate_design = Design.objects.create(
                user=request.user,
                brand=current_brand,
                name=f"{original_design.name} (Copy)",
                product=original_design.product,
                data=original_design.data,
                thumbnail_front=original_design.thumbnail_front,
                thumbnail_back=original_design.thumbnail_back,
                thumbnail_left=original_design.thumbnail_left,
                thumbnail_right=original_design.thumbnail_right,
                public=False  # Always create as private
            )
            
            # Redirect to the designer with the new design
            return redirect(f'/designer/?product={original_design.product}&design={duplicate_design.id}')
        except (ValueError, Design.DoesNotExist):
            pass
    
    # Load template data if template ID is provided
    template_data = None
    if template_id:
        try:
            template_id = int(template_id)
            template = DesignTemplate.objects.get(
                id=template_id,
                brand=current_brand,
                is_active=True
            )
            template_data = {
                'id': template.id,
                'name': template.name,
                'product': template.product,
                'design_data': template.design_data,
                'thumbnails': {
                    'front': template.thumbnail_front,
                    'back': template.thumbnail_back,
                    'left': template.thumbnail_left,
                    'right': template.thumbnail_right
                }
            }
        except (ValueError, DesignTemplate.DoesNotExist):
            pass
    
    # Load template for editing if template_edit_id is provided
    if template_edit_id and is_brand_owner:
        try:
            template_edit_id = int(template_edit_id)
            template = DesignTemplate.objects.get(
                id=template_edit_id,
                brand=current_brand
            )
            template_data = {
                'id': template.id,
                'name': template.name,
                'product': template.product,
                'design_data': template.design_data,
                'thumbnails': {
                    'front': template.thumbnail_front,
                    'back': template.thumbnail_back,
                    'left': template.thumbnail_left,
                    'right': template.thumbnail_right
                },
                'is_editing': True
            }
        except (ValueError, DesignTemplate.DoesNotExist):
            pass
    
    # Convert static product dict to ensure JavaScript compatibility
    def product_to_dict(product):
        if not product:
            return None
        # Static product is already a dict, just return it
        return product
    
    # Get brand backgrounds
    brand_backgrounds = []
    if current_brand:
        backgrounds = BrandBackground.objects.filter(
            brand=current_brand,
            is_active=True
        ).order_by('sort_order', 'name')
        
        brand_backgrounds = [
            {
                'id': bg.id,
                'name': bg.name,
                'image_url': bg.image_url,
                'thumbnail_url': bg.thumbnail_url,
                'is_default': bg.is_default,
            }
            for bg in backgrounds
        ]
    
    context = {
        'page_title': 'Designer',
        'current_brand': current_brand,
        'user': request.user if request.user.is_authenticated else None,
        'is_guest': not request.user.is_authenticated,
        'is_brand_owner': is_brand_owner,
        'current_product': current_product,  # Raw product object for template HTML
        'current_product_json': json.dumps(product_to_dict(current_product)) if current_product else 'null',  # JSON for JavaScript
        'product_id': product_id,
        'design_data': json.dumps(design_data) if design_data else None,
        'template_data': json.dumps(template_data) if template_data else None,
        'create_template': create_template,
        'bumpmaps': json.dumps(BUMPMAPS_DATA),
        'fonts': json.dumps(FONTS_DATA),
        'fonts_list': FONTS_DATA,  # Pass the raw list for template iteration
        'brand_backgrounds': json.dumps(brand_backgrounds),
    }
    
    return render(request, 'designer/designer.html', context)


@require_http_methods(["POST"])
def save_design(request):
    """Save or update a design"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request data'})
    
    # Get current brand
    current_brand = request.brand
    
    # Validate required fields
    required_fields = ['name', 'product', 'data']
    for field in required_fields:
        if field not in data or not data[field]:
            return JsonResponse({'success': False, 'error': f'Missing required field: {field}'})
    
    # Extract design data
    design_id = data.get('design_id')
    name = data['name']
    product = int(data['product'])
    thumbnail_front = data.get('thumbnail_front', '')
    thumbnail_back = data.get('thumbnail_back', '')
    thumbnail_left = data.get('thumbnail_left', '')
    thumbnail_right = data.get('thumbnail_right', '')
    is_public = bool(data.get('public', 0))
    design_data = data['data']
    
    if not request.user.is_authenticated:
        # Handle guest design save
        if 'guest_designs' not in request.session:
            request.session['guest_designs'] = []
        
        guest_design = {
            'id': design_id or f'temp_{uuid.uuid4().hex[:8]}',
            'name': name,
            'product_id': product,
            'design_data': design_data,
            'screenshots': {
                'front': thumbnail_front,
                'back': thumbnail_back,
                'left': thumbnail_left,
                'right': thumbnail_right
            },
            'public': is_public,
            'brand_id': current_brand.id,
            'created_at': timezone.now()
        }
        
        # Update or add the design
        designs = request.session['guest_designs']
        updated = False
        for i, d in enumerate(designs):
            if d.get('id') == design_id:
                designs[i] = guest_design
                updated = True
                break
        
        if not updated:
            designs.append(guest_design)
        
        request.session['guest_designs'] = designs
        request.session.modified = True
        
        return JsonResponse({
            'success': True,
            'design_id': guest_design['id'],
            'is_temporary': True,
            'message': 'Design saved temporarily. Create an account to save permanently.'
        })
    
    else:
        # Handle logged-in user design save
        try:
            if design_id and str(design_id).isdigit():
                # Update existing design
                design = Design.objects.get(id=design_id, user=request.user)
                design.name = name
                design.product = product
                design.thumbnail_front = thumbnail_front
                design.thumbnail_back = thumbnail_back
                design.thumbnail_left = thumbnail_left
                design.thumbnail_right = thumbnail_right
                design.data = design_data
                design.public = is_public
                design.save()
            else:
                # Create new design
                design = Design.objects.create(
                    user=request.user,
                    brand=current_brand,
                    name=name,
                    product=product,
                    thumbnail_front=thumbnail_front,
                    thumbnail_back=thumbnail_back,
                    thumbnail_left=thumbnail_left,
                    thumbnail_right=thumbnail_right,
                    data=design_data,
                    public=is_public
                )
            
            return JsonResponse({
                'success': True,
                'design_id': design.id,
                'message': 'Design saved successfully!'
            })
            
        except Design.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Design not found or access denied'})
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower():
                return JsonResponse({'success': False, 'error': 'A design with this name already exists. Please choose a different name.'})
            raise


def design_share(request, design_id):
    """View for shared design page"""
    try:
        design = get_object_or_404(Design, id=design_id)
        
        # Get the brand associated with the design
        brand = design.brand
        
        # Get the user who created the design
        designer = design.user
        
        # Get product info
        product_info = get_product_by_id(design.product)
        
        context = {
            'page_title': f"{design.name} - Shared Design",
            'design': design,
            'brand': brand,
            'designer': designer,
            'product_info': product_info,
            'design_data': design.data,
            'current_user': request.user if request.user.is_authenticated else None,
            'current_brand': request.brand,
        }
        
        return render(request, 'designer/design_share.html', context)
        
    except Design.DoesNotExist:
        return redirect('/404')


@login_required
def my_designs(request):
    """View for user's saved designs"""
    designs = Design.objects.filter(
        user=request.user,
        brand=request.brand
    ).order_by('-updated_at')
    
    context = {
        'page_title': 'My Designs',
        'designs': designs,
        'current_brand': request.brand,
    }
    
    return render(request, 'designer/my_designs.html', context)


def select_template(request):
    """View for selecting design templates"""
    templates = DesignTemplate.objects.filter(
        brand=request.brand,
        is_active=True
    ).order_by('sort_order', '-created_at')
    
    product_id = request.GET.get('product', 0)
    
    context = {
        'page_title': 'Select Template',
        'templates': templates,
        'product_id': product_id,
        'current_brand': request.brand,
    }
    
    return render(request, 'designer/select_template.html', context)