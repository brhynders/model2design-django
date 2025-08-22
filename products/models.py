from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import json


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Product Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category', kwargs={'category_slug': self.slug})


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    model_link = models.CharField(max_length=500)
    thumbnail = models.CharField(max_length=500, blank=True)
    categories = models.ManyToManyField(ProductCategory, blank=True)
    initial_layer = models.CharField(max_length=100, default='Front')
    initial_bumpmap = models.CharField(max_length=100, default='Polyester')
    can_order = models.BooleanField(default=True)
    
    # JSON fields for complex data
    sizes = models.JSONField(default=list, blank=True)
    prices = models.JSONField(default=dict, blank=True) 
    supported_bumpmaps = models.JSONField(default=list, blank=True)
    product_details = models.JSONField(default=list, blank=True)
    mesh_settings = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'pk': self.pk})
    
    def get_category_names(self):
        return list(self.categories.values_list('name', flat=True))
    
    def get_base_price(self):
        if self.prices and '1' in self.prices:
            return float(self.prices['1'])
        elif self.prices:
            return float(min(self.prices.values()))
        return 19.99
    
    def get_min_price(self):
        if self.prices:
            return float(min(self.prices.values()))
        return 19.99
    
    def get_price_breaks(self):
        """Return price breaks as dict for bulk pricing display"""
        if self.prices:
            return {int(k): float(v) for k, v in self.prices.items()}
        return {1: 19.99}
    
    def get_sizes(self):
        """Return available sizes"""
        return self.sizes or []


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image"


class BrandProduct(models.Model):
    """
    Through model for brand-specific product availability and pricing
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    custom_prices = models.JSONField(default=dict, blank=True, 
                                   help_text="Override default product prices for this brand")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['product', 'brand']
        verbose_name = "Brand Product"
        verbose_name_plural = "Brand Products"
    
    def __str__(self):
        return f"{self.brand.name} - {self.product.name}"
    
    def get_price(self, quantity=1):
        """Get price for this quantity, with brand-specific override if available"""
        if self.custom_prices:
            # Find the best price tier for this quantity from custom prices
            available_qtys = [int(q) for q in self.custom_prices.keys() if int(q) <= quantity]
            if available_qtys:
                best_qty = max(available_qtys)
                return float(self.custom_prices[str(best_qty)])
        
        # Fall back to product's default pricing
        return self.product.get_base_price()
    
    @property
    def price(self):
        """Default price for template display"""
        return self.get_price(1)
    
    @property
    def commission_rate(self):
        """Commission rate percentage (default 15%)"""
        return 15.0
    
    @property
    def commission_amount(self):
        """Commission amount based on price and rate"""
        return self.price * (self.commission_rate / 100)
    
    @property
    def total_sales(self):
        """Total number of sales (placeholder)"""
        return 0
    
    @property
    def total_revenue(self):
        """Total revenue generated (placeholder)"""
        return 0
