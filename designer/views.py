from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
from .models import Design, DesignTemplate, DesignShare, DesignImage
from brands.models import Brand, BrandBackground, BrandImageCategory, BrandImage
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
    if design_id:
        try:
            if request.user.is_authenticated:
                # Try to load user's design
                design = Design.objects.get(id=design_id, user=request.user)
            else:
                # Try to load guest's design using session_id
                if not request.session.session_key:
                    request.session.create()
                design = Design.objects.get(id=design_id, session_id=request.session.session_key)
            
            design_data = {
                'id': design.id,
                'name': design.name,
                'product_id': design.product,
                'design_data': design.data,
                'screenshots': {
                    'front': design.thumbnail_front.url if design.thumbnail_front else '',
                    'back': design.thumbnail_back.url if design.thumbnail_back else '',
                    'left': design.thumbnail_left.url if design.thumbnail_left else '',
                    'right': design.thumbnail_right.url if design.thumbnail_right else ''
                }
            }
        except Design.DoesNotExist:
            pass
    
    # Load template data if template ID is provided
    template_data = None
    is_editing_template = False
    
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
    elif template_edit_id and is_brand_owner:
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
                }
            }
            is_editing_template = True
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
    
    # Get image categories for image bank
    image_categories = []
    if current_brand:
        categories = BrandImageCategory.objects.filter(brand=current_brand).order_by('name')
        image_categories = [
            {
                'id': cat.id,
                'name': cat.name,
                'slug': cat.slug,
                'description': cat.description,
            }
            for cat in categories
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
        'is_editing_template': is_editing_template,
        'create_template': create_template,
        'bumpmaps': json.dumps(BUMPMAPS_DATA),
        'fonts': json.dumps(FONTS_DATA),
        'fonts_list': FONTS_DATA,  # Pass the raw list for template iteration
        'brand_backgrounds': json.dumps(brand_backgrounds),
        'image_categories': json.dumps(image_categories),
    }
    
    return render(request, 'designer/designer.html', context)



@require_http_methods(["POST"])
def save_design(request):
    """Save or update a design"""
    # Get current brand
    current_brand = getattr(request, 'brand', None)
    
    # Validate required fields from form data
    required_fields = ['name', 'product', 'data']
    for field in required_fields:
        if field not in request.POST or not request.POST.get(field):
            return JsonResponse({'success': False, 'error': f'Missing required field: {field}'})
    
    try:
        # Extract design data from form
        design_id = request.POST.get('design_id')
        name = request.POST.get('name')
        product = int(request.POST.get('product'))
        is_public = request.POST.get('public') == '1'  # '1' for true, '0' for false
        design_data = json.loads(request.POST.get('data'))  # Parse JSON from form field
        
        # Get uploaded thumbnail files directly (no base64 processing needed!)
        thumbnail_front = request.FILES.get('thumbnail_front')
        thumbnail_back = request.FILES.get('thumbnail_back')
        thumbnail_left = request.FILES.get('thumbnail_left')
        thumbnail_right = request.FILES.get('thumbnail_right')
    except (ValueError, json.JSONDecodeError) as e:
        return JsonResponse({'success': False, 'error': f'Invalid request data: {str(e)}'})
    
    # Clean design data - remove texture properties from decals
    if isinstance(design_data, dict) and 'layers' in design_data:
        for layer_name, layer_data in design_data['layers'].items():
            if isinstance(layer_data, dict) and 'decals' in layer_data:
                for decal in layer_data['decals']:
                    if isinstance(decal, dict) and 'texture' in decal:
                        del decal['texture']
    
    if not request.user.is_authenticated:
        # Handle guest design save - save to database with session_id
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        
        session_id = request.session.session_key
        
        try:
            if design_id and str(design_id).isdigit():
                # Update existing guest design
                design = Design.objects.get(id=design_id, session_id=session_id)
                design.name = name
                design.product = product
                design.brand = current_brand
                # Only update thumbnails if new ones were provided (files come directly from request.FILES)
                if thumbnail_front:
                    design.thumbnail_front = thumbnail_front
                if thumbnail_back:
                    design.thumbnail_back = thumbnail_back
                if thumbnail_left:
                    design.thumbnail_left = thumbnail_left
                if thumbnail_right:
                    design.thumbnail_right = thumbnail_right
                design.data = design_data
                design.public = is_public
                design.save()
            else:
                # Create new guest design
                design_kwargs = {
                    'session_id': session_id,
                    'brand': current_brand,
                    'name': name,
                    'product': product,
                    'data': design_data,
                    'public': is_public
                }
                # Only add thumbnails if they exist (files come directly from request.FILES)
                if thumbnail_front:
                    design_kwargs['thumbnail_front'] = thumbnail_front
                if thumbnail_back:
                    design_kwargs['thumbnail_back'] = thumbnail_back
                if thumbnail_left:
                    design_kwargs['thumbnail_left'] = thumbnail_left
                if thumbnail_right:
                    design_kwargs['thumbnail_right'] = thumbnail_right
                
                design = Design.objects.create(**design_kwargs)
            
            return JsonResponse({
                'success': True,
                'design_id': design.id,
                'is_temporary': False,
                'message': 'Design saved successfully!',
                'redirect_url': '/designer/my-designs/'
            })
            
        except Design.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Design not found or access denied'})
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower():
                return JsonResponse({'success': False, 'error': 'A design with this name already exists. Please choose a different name.'})
            return JsonResponse({'success': False, 'error': f'Database error: {str(e)}'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    else:
        # Handle logged-in user design save
        try:
            if design_id and str(design_id).isdigit():
                # Update existing design
                design = Design.objects.get(id=design_id, user=request.user)
                design.name = name
                design.product = product
                design.brand = current_brand
                # Only update thumbnails if new ones were provided (files come directly from request.FILES)
                if thumbnail_front:
                    design.thumbnail_front = thumbnail_front
                if thumbnail_back:
                    design.thumbnail_back = thumbnail_back
                if thumbnail_left:
                    design.thumbnail_left = thumbnail_left
                if thumbnail_right:
                    design.thumbnail_right = thumbnail_right
                design.data = design_data
                design.public = is_public
                design.save()
            else:
                # Create new design
                design_kwargs = {
                    'user': request.user,
                    'brand': current_brand,
                    'name': name,
                    'product': product,
                    'data': design_data,
                    'public': is_public
                }
                # Only add thumbnails if they exist (files come directly from request.FILES)
                if thumbnail_front:
                    design_kwargs['thumbnail_front'] = thumbnail_front
                if thumbnail_back:
                    design_kwargs['thumbnail_back'] = thumbnail_back
                if thumbnail_left:
                    design_kwargs['thumbnail_left'] = thumbnail_left
                if thumbnail_right:
                    design_kwargs['thumbnail_right'] = thumbnail_right
                
                design = Design.objects.create(**design_kwargs)
            
            return JsonResponse({
                'success': True,
                'design_id': design.id,
                'message': 'Design saved successfully!',
                'redirect_url': '/designer/my-designs/'
            })
            
        except Design.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Design not found or access denied'})
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower():
                return JsonResponse({'success': False, 'error': 'A design with this name already exists. Please choose a different name.'})
            return JsonResponse({'success': False, 'error': f'Database error: {str(e)}'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})


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


def my_designs(request):
    """View for user's saved designs - supports both guest and authenticated users"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from datetime import datetime, timedelta
    import json
    
    current_brand = getattr(request, 'brand', None)
    is_guest = not request.user.is_authenticated
    
    # Get query parameters
    search = request.GET.get('search', '').strip()
    order_by = request.GET.get('order', 'updated_desc')
    page = request.GET.get('page', 1)
    per_page = 9
    
    if is_guest:
        # Handle guest designs from database using session_id
        if not request.session.session_key:
            request.session.create()
        
        session_id = request.session.session_key
        designs_queryset = Design.objects.filter(
            session_id=session_id,
            brand=current_brand
        )
    else:
        # Handle authenticated user designs
        designs_queryset = Design.objects.filter(
            user=request.user,
            brand=current_brand
        )
    
    # Apply search filter
    if search:
        designs_queryset = designs_queryset.filter(name__icontains=search)
    
    # Apply ordering
    order_field = '-updated_at'  # default
    if order_by == 'updated_asc':
        order_field = 'updated_at'
    elif order_by == 'created_desc':
        order_field = '-created_at'
    elif order_by == 'created_asc':
        order_field = 'created_at'
    elif order_by == 'name_asc':
        order_field = 'name'
    elif order_by == 'name_desc':
        order_field = '-name'
    
    designs_queryset = designs_queryset.order_by(order_field)
    
    # Pagination
    paginator = Paginator(designs_queryset, per_page)
    try:
        designs_paginated = paginator.page(page)
    except:
        designs_paginated = paginator.page(1)
    
    # Calculate statistics
    all_designs = designs_queryset.all()
    total_designs = all_designs.count()
    
    # Recent designs (last week)
    one_week_ago = datetime.now() - timedelta(days=7)
    recent_designs = all_designs.filter(created_at__gte=one_week_ago).count()
    
    # Unique products designed
    unique_products = all_designs.values_list('product', flat=True).distinct().count()
    
    context = {
        'page_title': 'My Designs',
        'designs': designs_paginated,
        'current_brand': current_brand,
        'is_guest': is_guest,
        'search': search,
        'order_by': order_by,
        'total_designs': total_designs,
        'recent_designs': recent_designs,
        'products_designed': unique_products,
        'has_search_or_filter': bool(search) or order_by != 'updated_desc',
        'products_data': json.dumps(PRODUCTS_DATA),  # For JavaScript
        'bumpmaps_data': json.dumps(BUMPMAPS_DATA),
        'fonts_data': json.dumps(FONTS_DATA),
    }
    
    return render(request, 'designer/my_designs.html', context)


@require_http_methods(["POST"])
def update_design_visibility(request, design_id):
    """Update design visibility (public/private)"""
    from django.http import JsonResponse
    import json
    
    current_brand = getattr(request, 'brand', None)
    is_guest = not request.user.is_authenticated
    
    try:
        data = json.loads(request.body)
        is_public = bool(data.get('public', False))
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid request data'})
    
    try:
        if is_guest:
            # Handle guest design visibility update using session_id
            if not request.session.session_key:
                return JsonResponse({'success': False, 'error': 'No active session'})
            
            design = Design.objects.get(
                id=design_id, 
                session_id=request.session.session_key,
                brand=current_brand
            )
        else:
            # Handle authenticated user design visibility update
            design = Design.objects.get(
                id=design_id, 
                user=request.user,
                brand=current_brand
            )
        
        # Update visibility
        design.public = is_public
        design.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Design {"made public" if is_public else "made private"} successfully',
            'is_public': is_public
        })
        
    except Design.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Design not found or access denied'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})


@require_http_methods(["DELETE"])
def delete_design(request, design_id):
    """Delete a design"""
    from django.http import JsonResponse
    import json
    
    current_brand = getattr(request, 'brand', None)
    is_guest = not request.user.is_authenticated
    
    try:
        if is_guest:
            # Handle guest design deletion using session_id
            if not request.session.session_key:
                return JsonResponse({'success': False, 'error': 'No active session'})
            
            design = Design.objects.get(
                id=design_id, 
                session_id=request.session.session_key,
                brand=current_brand
            )
        else:
            # Handle authenticated user design deletion
            design = Design.objects.get(
                id=design_id, 
                user=request.user,
                brand=current_brand
            )
        
        # Delete the design
        design.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Design deleted successfully'
        })
        
    except Design.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Design not found or access denied'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})


@login_required
def copy_design(request, design_id):
    """Copy a public design to the current user's account"""
    current_brand = getattr(request, 'brand', None)
    
    try:
        original_design = get_object_or_404(Design, id=design_id, public=True)
        
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
        
        messages.success(request, f'Design "{original_design.name}" has been copied to your account.')
        
        # Redirect to the designer with the new design
        return redirect(f'/designer/?product={original_design.product}&design={duplicate_design.id}')
    except Design.DoesNotExist:
        messages.error(request, 'Design not found or not available for copying.')
        return redirect('/designer/')


def load_template(request, template_id):
    """Load a template for use in the designer"""
    current_brand = getattr(request, 'brand', None)
    
    try:
        template = get_object_or_404(
            DesignTemplate,
            id=template_id,
            brand=current_brand,
            is_active=True
        )
        
        # Redirect to designer with template
        return redirect(f'/designer/?product={template.product}&template={template.id}')
    except DesignTemplate.DoesNotExist:
        messages.error(request, 'Template not found.')
        return redirect('/designer/')


@login_required
def edit_template(request, template_id):
    """Edit an existing template (brand owners only)"""
    current_brand = getattr(request, 'brand', None)
    
    # Check if user is a brand owner
    if not request.user.is_brand_owner:
        messages.error(request, 'You must be a brand owner to edit templates.')
        return redirect('/designer/')
    
    try:
        template = get_object_or_404(
            DesignTemplate,
            id=template_id,
            brand=current_brand
        )
        
        # Redirect to designer with template edit mode
        return redirect(f'/designer/?product={template.product}&template_edit={template.id}')
    except DesignTemplate.DoesNotExist:
        messages.error(request, 'Template not found.')
        return redirect('/designer/')


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


@require_http_methods(["GET"])
def user_images_api(request):
    """API endpoint to get user's design images and brand images"""
    try:
        image_data = []
        
        # Get user uploaded images (DesignImage)
        if request.user.is_authenticated:
            user_images = DesignImage.objects.filter(user=request.user)
        else:
            # For guest users, use session ID
            session_key = request.session.session_key
            if not session_key:
                # Create session if it doesn't exist
                request.session.create()
                session_key = request.session.session_key
            
            user_images = DesignImage.objects.filter(session_id=session_key)
        
        # Add user uploaded images
        for img in user_images:
            image_data.append({
                'id': f'user_{img.id}',
                'name': img.name,
                'image_url': img.image.url,
                'thumbnail_url': img.thumbnail.url if img.thumbnail else img.image.url,
                'width': img.width,
                'height': img.height,
                'file_size': img.file_size,
                'filetype': img.filetype,
                'created_at': img.created_at.isoformat(),
                'source': 'user',
                'category_id': None
            })
        
        # Get brand images
        current_brand = request.brand
        if current_brand:
            brand_images = BrandImage.objects.filter(brand=current_brand).select_related('category')
            
            for img in brand_images:
                image_data.append({
                    'id': f'brand_{img.id}',
                    'name': img.name,
                    'image_url': img.image_url,
                    'thumbnail_url': img.thumbnail_url or img.image_url,
                    'width': img.width,
                    'height': img.height,
                    'file_size': img.file_size,
                    'filetype': 'jpg',  # Default for brand images
                    'created_at': img.created_at.isoformat(),
                    'source': 'brand',
                    'category_id': img.category.id if img.category else None
                })
        
        return JsonResponse({
            'success': True,
            'images': image_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def upload_image_api(request):
    """API endpoint to upload new design images (supports multiple files)"""
    try:
        # Check if image files are provided
        if 'images' not in request.FILES and 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No image files provided'
            }, status=400)
        
        # Get image files - support both 'images' (multiple) and 'image' (single) keys
        image_files = []
        if 'images' in request.FILES:
            image_files = request.FILES.getlist('images')
        elif 'image' in request.FILES:
            image_files = [request.FILES['image']]
        
        if not image_files:
            return JsonResponse({
                'success': False,
                'error': 'No image files provided'
            }, status=400)
        
        # Validate file types and sizes
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/avif']
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        
        uploaded_images = []
        errors = []
        
        # Get session info once
        session_key = None
        if not request.user.is_authenticated:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
        
        for image_file in image_files:
            try:
                # Validate file type
                if image_file.content_type not in allowed_types:
                    errors.append(f'{image_file.name}: Invalid file type. Please upload a JPEG, PNG, GIF, or WebP image.')
                    continue
                
                # Validate file size
                if image_file.size > max_size:
                    errors.append(f'{image_file.name}: File too large. Maximum size is 10MB.')
                    continue
                
                # Additional check for extremely large images
                from PIL import Image as PILImage
                try:
                    # Open the image to check dimensions
                    img = PILImage.open(image_file)
                    width, height = img.size
                    total_pixels = width * height
                    
                    # Check if image has too many pixels (over 100 megapixels as a reasonable limit)
                    if total_pixels > 100000000:  # 100 million pixels
                        errors.append(f'{image_file.name}: Image resolution too high ({width}x{height}). Please resize to under 100 megapixels.')
                        continue
                    
                    # Reset file pointer after PIL opens it
                    image_file.seek(0)
                except Exception as pil_error:
                    errors.append(f'{image_file.name}: Could not process image. It may be corrupted or too large.')
                    continue
                
                # Create DesignImage instance
                name = request.POST.get('name', image_file.name)
                design_image = DesignImage(
                    name=name,
                    image=image_file
                )
                
                # Set user or session_id
                if request.user.is_authenticated:
                    design_image.user = request.user
                else:
                    design_image.session_id = session_key
                
                # Validate and save
                design_image.full_clean()
                design_image.save()
                
                # Add to successful uploads
                uploaded_images.append({
                    'id': f'user_{design_image.id}',
                    'name': design_image.name,
                    'image_url': design_image.image.url,
                    'thumbnail_url': design_image.thumbnail.url if design_image.thumbnail else design_image.image.url,
                    'width': design_image.width,
                    'height': design_image.height,
                    'file_size': design_image.file_size,
                    'filetype': design_image.filetype,
                    'created_at': design_image.created_at.isoformat(),
                    'source': 'user',
                    'category_id': None
                })
                
            except ValidationError as e:
                errors.append(f'{image_file.name}: {str(e)}')
            except Exception as e:
                errors.append(f'{image_file.name}: {str(e)}')
        
        # Return results
        if uploaded_images:
            response_data = {
                'success': True,
                'images': uploaded_images,
                'uploaded_count': len(uploaded_images)
            }
            if errors:
                response_data['errors'] = errors
                response_data['error_count'] = len(errors)
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'No images could be uploaded',
                'errors': errors
            }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["DELETE"])
def delete_image_api(request, image_id):
    """API endpoint to delete a user's design image"""
    try:
        # Extract the actual ID from the prefixed ID (e.g., "user_123" -> 123)
        if image_id.startswith('user_'):
            actual_id = image_id.replace('user_', '')
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid image ID format'
            }, status=400)
        
        try:
            actual_id = int(actual_id)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid image ID'
            }, status=400)
        
        # Get the image - ensure it belongs to the current user/session
        if request.user.is_authenticated:
            image = DesignImage.objects.get(id=actual_id, user=request.user)
        else:
            # For guest users, check session
            session_key = request.session.session_key
            if not session_key:
                return JsonResponse({
                    'success': False,
                    'error': 'No session found'
                }, status=400)
            image = DesignImage.objects.get(id=actual_id, session_id=session_key)
        
        # Delete the database entry (not the actual file)
        image_name = image.name
        image.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Image "{image_name}" deleted successfully'
        })
        
    except DesignImage.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Image not found or access denied'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


