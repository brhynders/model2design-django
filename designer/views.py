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
import uuid
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


@require_http_methods(["POST"])
def save_design(request):
    """Save a design (supports both authenticated users and guests)"""
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Get design info
        name = data.get('name', 'Untitled Design')
        product_id = data.get('product')
        design_data = data.get('data', {})
        session_id = data.get('session_id')
        public = data.get('public', False)
        
        # Validate required fields
        if not name.strip():
            return JsonResponse({
                'success': False,
                'error': 'Design name is required'
            }, status=400)
            
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'Product ID is required'
            }, status=400)
            
        if not design_data:
            return JsonResponse({
                'success': False,
                'error': 'Design data is required'
            }, status=400)
        
        # Create design instance
        design = Design(
            name=name.strip(),
            product=product_id,
            data=design_data,
            public=public
        )
        
        # Set user or session_id
        if request.user.is_authenticated:
            design.user = request.user
        else:
            # For guest users, use session ID
            if not session_id:
                session_id = request.session.session_key
                if not session_id:
                    # Create session if it doesn't exist
                    request.session.save()
                    session_id = request.session.session_key
            design.session_id = session_id
        
        # Save the design
        design.save()
        
        return JsonResponse({
            'success': True,
            'design_id': design.id,
            'message': f'Design "{name}" saved successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)