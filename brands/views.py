from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.text import slugify

from .models import (
    Brand, BrandOwner, BrandTemplate, BrandImage, 
    BrandImageCategory, BrandEarnings, PartnerRequest
)
from .mixins import BrandFilterMixin
from .forms import PartnerRequestForm
from products.models import BrandProduct
from django.core.mail import send_mail
from django.conf import settings


class BrandOwnerRequiredMixin(LoginRequiredMixin):
    """Mixin to require brand ownership for access"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        # Check if user owns any brands
        if not BrandOwner.objects.filter(user=request.user).exists():
            messages.error(request, "You don't have access to any brand management areas.")
            return redirect('accounts:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_user_brands(self):
        """Get brands owned by current user"""
        return Brand.objects.filter(
            owners__user=self.request.user,
            is_active=True
        ).distinct()
    
    def get_current_brand(self):
        """Get current brand from session or default"""
        user_brands = self.get_user_brands()
        selected_brand_id = self.request.session.get('selected_brand_id')
        current_brand = None
        
        if selected_brand_id:
            current_brand = user_brands.filter(id=selected_brand_id).first()
        
        if not current_brand:
            primary_brand = user_brands.filter(owners__is_primary=True, owners__user=self.request.user).first()
            current_brand = primary_brand or user_brands.first()
        
        return current_brand
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_brands'] = self.get_user_brands()
        context['current_brand'] = self.get_current_brand()
        return context


@login_required
def brand_dashboard(request):
    """Brand owner dashboard"""
    user_brands = Brand.objects.filter(
        owners__user=request.user,
        is_active=True
    ).distinct()
    
    if not user_brands.exists():
        messages.error(request, "You don't have access to any brand management areas.")
        return redirect('accounts:dashboard')
    
    # Get current brand from session, primary brand, or first brand
    selected_brand_id = request.session.get('selected_brand_id')
    current_brand = None
    
    if selected_brand_id:
        current_brand = user_brands.filter(id=selected_brand_id).first()
    
    if not current_brand:
        primary_brand = user_brands.filter(owners__is_primary=True, owners__user=request.user).first()
        current_brand = primary_brand or user_brands.first()
    
    # Dashboard statistics
    total_products = BrandProduct.objects.filter(brand=current_brand, is_available=True).count()
    total_templates = BrandTemplate.objects.filter(brand=current_brand).count()
    total_images = BrandImage.objects.filter(brand=current_brand).count()
    
    # Recent earnings (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_earnings = BrandEarnings.objects.filter(
        brand=current_brand,
        transaction_date__gte=thirty_days_ago
    ).aggregate(
        total=Sum('commission_amount'),
        count=Count('id')
    )
    
    # Recent templates
    recent_templates = BrandTemplate.objects.filter(brand=current_brand).order_by('-created_at')[:5]
    
    context = {
        'current_brand': current_brand,
        'user_brands': user_brands,
        'total_products': total_products,
        'total_templates': total_templates,
        'total_images': total_images,
        'recent_earnings': recent_earnings,
        'recent_templates': recent_templates,
    }
    
    return render(request, 'brands/dashboard.html', context)


class BrandTemplateListView(BrandOwnerRequiredMixin, ListView):
    """List brand templates"""
    model = BrandTemplate
    template_name = 'brands/templates.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        brands = self.get_user_brands()
        return BrandTemplate.objects.filter(brand__in=brands).order_by('-created_at')
    
    def post(self, request, *args, **kwargs):
        """Handle template creation, editing, and deletion"""
        action = request.POST.get('action')
        brands = self.get_user_brands()
        
        if action == 'create':
            name = request.POST.get('name')
            brand_id = request.POST.get('brand')
            description = request.POST.get('description', '')
            template_data = request.POST.get('template_data', '')
            
            # Validate brand ownership
            brand = get_object_or_404(brands, id=brand_id)
            
            # Create template
            template = BrandTemplate.objects.create(
                name=name,
                description=description,
                template_data=template_data,
                brand=brand
            )
            messages.success(request, f"Template '{name}' created successfully!")
            
        elif action == 'delete':
            template_id = request.POST.get('template_id')
            template = get_object_or_404(BrandTemplate, id=template_id, brand__in=brands)
            
            template_name = template.name
            template.delete()
            messages.success(request, f"Template '{template_name}' deleted successfully!")
        
        return redirect('brands:templates')


class BrandImageListView(BrandOwnerRequiredMixin, ListView):
    """List brand images"""
    model = BrandImage
    template_name = 'brands/images.html'
    context_object_name = 'images'
    paginate_by = 24
    
    def get_queryset(self):
        brands = self.get_user_brands()
        queryset = BrandImage.objects.filter(brand__in=brands).order_by('-created_at')
        
        # Filter by category if specified
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brands = self.get_user_brands()
        context['categories'] = BrandImageCategory.objects.filter(brand__in=brands)
        context['selected_category'] = self.request.GET.get('category', '')
        return context


class BrandImageCategoryListView(BrandOwnerRequiredMixin, ListView):
    """Manage brand image categories"""
    model = BrandImageCategory
    template_name = 'brands/image_categories.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        brands = self.get_user_brands()
        return BrandImageCategory.objects.filter(brand__in=brands).order_by('name')
    
    
    def post(self, request, *args, **kwargs):
        """Handle category creation, editing, and deletion"""
        action = request.POST.get('action')
        brands = self.get_user_brands()
        
        if action == 'create':
            name = request.POST.get('name')
            brand_id = request.POST.get('brand')
            description = request.POST.get('description', '')
            
            # Validate brand ownership
            brand = get_object_or_404(brands, id=brand_id)
            
            # Create category
            slug = slugify(name)
            category = BrandImageCategory.objects.create(
                name=name,
                slug=slug,
                description=description,
                brand=brand
            )
            messages.success(request, f"Category '{name}' created successfully!")
            
        elif action == 'edit':
            category_id = request.POST.get('category_id')
            category = get_object_or_404(BrandImageCategory, id=category_id, brand__in=brands)
            
            category.name = request.POST.get('name', category.name)
            category.slug = request.POST.get('slug', category.slug)
            category.description = request.POST.get('description', category.description)
            category.save()
            
            messages.success(request, f"Category '{category.name}' updated successfully!")
            
        elif action == 'delete':
            category_id = request.POST.get('category_id')
            category = get_object_or_404(BrandImageCategory, id=category_id, brand__in=brands)
            
            category_name = category.name
            category.delete()
            messages.success(request, f"Category '{category_name}' deleted successfully!")
        
        return redirect('brands:image_categories')


@login_required
def brand_settings(request, brand_slug=None):
    """Brand settings management"""
    user_brands = Brand.objects.filter(
        owners__user=request.user,
        is_active=True
    ).distinct()
    
    if not user_brands.exists():
        messages.error(request, "You don't have access to any brand management areas.")
        return redirect('accounts:dashboard')
    
    # Get specific brand or default to first
    if brand_slug:
        current_brand = get_object_or_404(user_brands, slug=brand_slug)
    else:
        current_brand = user_brands.first()
    
    # Check if user has permission to edit this brand
    brand_owner = BrandOwner.objects.filter(
        user=request.user, 
        brand=current_brand
    ).first()
    
    if not brand_owner:
        raise Http404("Brand not found or access denied")
    
    # Handle POST request for updating brand settings
    if request.method == 'POST':
        # Update brand information
        current_brand.name = request.POST.get('name', current_brand.name)
        current_brand.subdomain = request.POST.get('subdomain', current_brand.subdomain)
        current_brand.contact_email = request.POST.get('contact_email', current_brand.contact_email)
        current_brand.website_url = request.POST.get('website_url', current_brand.website_url)
        current_brand.logo_url = request.POST.get('logo_url', current_brand.logo_url)
        current_brand.description = request.POST.get('description', current_brand.description)
        current_brand.primary_color = request.POST.get('primary_color', current_brand.primary_color)
        current_brand.secondary_color = request.POST.get('secondary_color', current_brand.secondary_color)
        current_brand.is_active = 'is_active' in request.POST
        
        current_brand.save()
        messages.success(request, "Brand settings updated successfully!")
        return redirect('brands:settings')
    
    context = {
        'current_brand': current_brand,
        'user_brands': user_brands,
        'brand_owner': brand_owner,
    }
    
    return render(request, 'brands/settings.html', context)


class BrandEarningsListView(BrandOwnerRequiredMixin, ListView):
    """Brand earnings and analytics"""
    model = BrandEarnings
    template_name = 'brands/earnings.html'
    context_object_name = 'earnings'
    paginate_by = 50
    
    def get_queryset(self):
        brands = self.get_user_brands()
        return BrandEarnings.objects.filter(brand__in=brands).order_by('-transaction_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brands = self.get_user_brands()
        
        # Earnings summary
        total_earnings = BrandEarnings.objects.filter(brand__in=brands).aggregate(
            total_amount=Sum('amount'),
            total_commission=Sum('commission_amount'),
            pending=Sum('commission_amount', filter=Q(payment_status='pending')),
            paid=Sum('commission_amount', filter=Q(payment_status='paid')),
        )
        
        # Monthly breakdown (last 12 months) - SQLite compatible
        from django.db.models import F
        from django.db.models.functions import TruncMonth
        
        twelve_months_ago = timezone.now() - timedelta(days=365)
        monthly_earnings = BrandEarnings.objects.filter(
            brand__in=brands,
            transaction_date__gte=twelve_months_ago
        ).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            total=Sum('commission_amount'),
            count=Count('id')
        ).order_by('month')
        
        context.update({
            'user_brands': brands,
            'total_earnings': total_earnings,
            'monthly_earnings': monthly_earnings,
        })
        
        return context


# API Views for AJAX requests
@login_required
def api_brand_templates(request):
    """API endpoint for brand templates"""
    user_brands = Brand.objects.filter(
        owners__user=request.user,
        is_active=True
    ).distinct()
    
    templates = BrandTemplate.objects.filter(
        brand__in=user_brands
    ).values('id', 'name', 'brand__name', 'thumbnail_url', 'is_public', 'usage_count')
    
    return JsonResponse({
        'templates': list(templates)
    })


@login_required
def api_public_templates(request):
    """API endpoint for public templates (available to all brands)"""
    templates = BrandTemplate.objects.filter(
        is_public=True,
        brand__is_active=True
    ).values(
        'id', 'name', 'brand__name', 'thumbnail_url', 'usage_count'
    ).order_by('-is_featured', '-usage_count')
    
    return JsonResponse({
        'templates': list(templates)
    })


@login_required
def api_brand_backgrounds(request):
    """API endpoint for brand background images"""
    user_brands = Brand.objects.filter(
        owners__user=request.user,
        is_active=True
    ).distinct()
    
    # Get background images (assume there's a category for backgrounds)
    background_images = BrandImage.objects.filter(
        brand__in=user_brands,
        category__slug='backgrounds'
    ).values('id', 'name', 'image_url', 'thumbnail_url', 'is_public')
    
    return JsonResponse({
        'backgrounds': list(background_images)
    })


class BrandCatalogView(BrandOwnerRequiredMixin, ListView):
    """Brand catalog - manage which products are available for this brand"""
    model = BrandProduct
    template_name = 'brands/catalog.html'
    context_object_name = 'brand_products'
    paginate_by = 20
    
    def get_queryset(self):
        brands = self.get_user_brands()
        return BrandProduct.objects.filter(brand__in=brands).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brands = self.get_user_brands()
        
        # Get product statistics
        total_products = BrandProduct.objects.filter(brand__in=brands).count()
        active_products = BrandProduct.objects.filter(brand__in=brands, is_available=True).count()
        
        context.update({
            'total_products': total_products,
            'active_products': active_products,
            'inactive_products': total_products - active_products,
            'estimated_revenue': active_products * 25,  # Estimate $25 per active product per month
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle product activation/deactivation"""
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        brands = self.get_user_brands()
        
        if action in ['activate', 'deactivate'] and product_id:
            product = get_object_or_404(BrandProduct, id=product_id, brand__in=brands)
            product.is_available = (action == 'activate')
            product.save()
            
            status = 'activated' if action == 'activate' else 'deactivated'
            messages.success(request, f"Product '{product.product.name}' {status} successfully!")
        
        return redirect('brands:catalog')


@login_required
def switch_brand(request, brand_slug):
    """Switch to a different brand"""
    user_brands = Brand.objects.filter(
        owners__user=request.user,
        is_active=True
    ).distinct()
    
    brand = get_object_or_404(user_brands, slug=brand_slug)
    
    # Store the selected brand in session
    request.session['selected_brand_id'] = brand.id
    
    # Redirect to dashboard with success message
    messages.success(request, f"Switched to {brand.name}")
    return redirect('brands:dashboard')


def partner_with_us(request):
    """Partner/Brand request page"""
    if request.method == 'POST':
        form = PartnerRequestForm(request.POST)
        if form.is_valid():
            partner_request = form.save()
            
            # Send notification email to admins
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
                
                if admin_emails:
                    subject = f"New Partner Request: {partner_request.business_name}"
                    message = f"""A new partner request has been submitted.

Business Name: {partner_request.business_name}
Contact Name: {partner_request.contact_name}
Email: {partner_request.email}
Phone: {partner_request.phone}
Website: {partner_request.website}
Business Type: {partner_request.get_business_type_display() if partner_request.business_type else 'Not specified'}
Expected Volume: {partner_request.get_expected_volume_display() if partner_request.expected_volume else 'Not specified'}
Message: {partner_request.message}

View in admin panel: {request.build_absolute_uri('/admin/brands/partnerrequest/')}{partner_request.id}/"""
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        admin_emails,
                        fail_silently=True,
                    )
            except Exception as e:
                # Log the error but don't fail the request
                pass
            
            # Send confirmation email to requester
            try:
                subject = "Thank you for your partnership request"
                message = f"""Dear {partner_request.contact_name},

Thank you for your interest in partnering with us.

We have received your request and our partnership team will review it shortly. You can expect to hear back from us within 1-2 business days.

If you have any urgent questions, please don't hesitate to contact us.

Best regards,
The Team"""
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [partner_request.email],
                    fail_silently=True,
                )
            except Exception as e:
                # Log the error but don't fail the request
                pass
            
            messages.success(request, "Thank you for your interest! We've received your partnership request and will get back to you within 1-2 business days.")
            return redirect('brands:partner')
    else:
        form = PartnerRequestForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'brands/partner.html', context)
