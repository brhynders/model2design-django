from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import json

User = get_user_model()


class Brand(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    subdomain = models.CharField(max_length=100, unique=True, blank=True, null=True, 
                                help_text="Leave empty for default brand (no subdomain)")
    headline = models.CharField(max_length=500, blank=True, help_text="Main headline for homepage")
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False, 
                                   help_text="Default brand for main domain")
    is_active = models.BooleanField(default=True)
    
    # Brand customization
    logo_url = models.CharField(max_length=500, blank=True)
    primary_color = models.CharField(max_length=7, default='#007bff', 
                                   help_text="Brand primary color (hex)")
    secondary_color = models.CharField(max_length=7, default='#6c757d', 
                                     help_text="Brand secondary color (hex)")
    
    # Contact information
    contact_email = models.EmailField(blank=True)
    website_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_brand'
            )
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Ensure only one default brand
        if self.is_default:
            Brand.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def get_domain(self):
        """Get the full domain for this brand"""
        if self.subdomain:
            return f"{self.subdomain}.example.com"  # Replace with actual domain
        return "example.com"
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB values"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return f"{int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}"
        return "13, 110, 253"  # Default Bootstrap primary RGB
    
    def get_brand_styles(self):
        """Generate CSS styles for brand customization"""
        primary_rgb = self.hex_to_rgb(self.primary_color)
        
        return f"""
        :root {{
            --brand-primary: {self.primary_color};
            --brand-secondary: {self.secondary_color};
            --brand-primary-rgb: {primary_rgb};
        }}
        .btn-primary {{
            background-color: var(--brand-primary);
            border-color: var(--brand-primary);
        }}
        .btn-primary:hover {{
            background-color: var(--brand-primary);
            border-color: var(--brand-primary);
            filter: brightness(0.9);
        }}
        .btn-outline-primary {{
            color: var(--brand-primary);
            border-color: var(--brand-primary);
        }}
        .btn-outline-primary:hover {{
            background-color: var(--brand-primary);
            border-color: var(--brand-primary);
            color: white;
        }}
        .btn-outline-primary:focus {{
            box-shadow: 0 0 0 0.2rem rgba(var(--brand-primary-rgb), 0.25);
        }}
        .nav-tabs .nav-link.active {{
            color: var(--brand-primary);
            border-color: var(--brand-primary) var(--brand-primary) transparent;
        }}
        .nav-tabs .nav-link:hover {{
            color: var(--brand-primary);
            border-color: var(--brand-primary) var(--brand-primary) transparent;
        }}
        .nav-pills .nav-link.active {{
            background-color: var(--brand-primary);
            border-color: var(--brand-primary);
        }}
        .nav-pills .nav-link:hover {{
            color: var(--brand-primary);
        }}
        .text-primary {{
            color: var(--brand-primary) !important;
        }}
        .bg-primary {{
            background-color: var(--brand-primary) !important;
        }}
        .border-primary {{
            border-color: var(--brand-primary) !important;
        }}
        .hover-text-primary:hover {{
            color: var(--brand-primary) !important;
        }}
        footer a:hover i {{
            color: var(--brand-primary) !important;
        }}
        """
    
    @classmethod
    def get_by_subdomain(cls, subdomain=None):
        """Get brand by subdomain, fallback to default"""
        if subdomain:
            try:
                return cls.objects.get(subdomain=subdomain, is_active=True)
            except cls.DoesNotExist:
                pass
        
        # Return default brand
        try:
            return cls.objects.get(is_default=True, is_active=True)
        except cls.DoesNotExist:
            # Create a default brand if none exists
            return cls.objects.create(
                name="Default Brand",
                is_default=True,
                is_active=True
            )


class BrandOwner(models.Model):
    """Brand ownership relationships"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='owners')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_brands')
    is_primary = models.BooleanField(default=False, help_text="Primary owner with full access")
    permissions = models.JSONField(default=dict, blank=True, help_text="Specific permissions for this owner")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['brand', 'user']
        verbose_name = "Brand Owner"
        verbose_name_plural = "Brand Owners"
    
    def __str__(self):
        return f"{self.user.email} owns {self.brand.name}"


class BrandImageCategory(models.Model):
    """Categories for brand images (backgrounds, logos, etc.)"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='image_categories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['brand', 'slug']
        verbose_name_plural = "Brand Image Categories"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.brand.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BrandImage(models.Model):
    """Brand images and assets"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='images')
    category = models.ForeignKey(BrandImageCategory, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    name = models.CharField(max_length=200)
    image_url = models.CharField(max_length=500)
    thumbnail_url = models.CharField(max_length=500, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_public = models.BooleanField(default=False, help_text="Available for public templates")
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="File size in bytes")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Brand Image"
        verbose_name_plural = "Brand Images"
    
    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class BrandTemplate(models.Model):
    """Brand-specific design templates"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template_data = models.JSONField(default=dict, help_text="3D design template data")
    thumbnail_url = models.CharField(max_length=500, blank=True)
    is_public = models.BooleanField(default=False, help_text="Available to other brands")
    is_featured = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = "Brand Template"
        verbose_name_plural = "Brand Templates"
    
    def __str__(self):
        return f"{self.brand.name} - {self.name}"
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class BrandEarnings(models.Model):
    """Track earnings/revenue for brands"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='earnings')
    order_id = models.PositiveIntegerField(help_text="Reference to order ID")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Commission percentage")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    transaction_date = models.DateTimeField()
    payment_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date']
        verbose_name = "Brand Earnings"
        verbose_name_plural = "Brand Earnings"
    
    def __str__(self):
        return f"{self.brand.name} - ${self.amount} ({self.payment_status})"
    
    def save(self, *args, **kwargs):
        if not self.commission_amount:
            self.commission_amount = (self.amount * self.commission_rate) / 100
        super().save(*args, **kwargs)
