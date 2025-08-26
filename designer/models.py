from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from brands.models import Brand

User = get_user_model()


class Design(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='designs')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='designs')
    name = models.CharField(max_length=255)
    product = models.IntegerField()  # References product ID from data.products.php
    data = models.JSONField()  # Stores the design data
    thumbnail_front = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_back = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_left = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_right = models.URLField(max_length=500, blank=True, null=True)
    public = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = [['user', 'brand', 'name']]

    def __str__(self):
        return f"{self.name} - {self.user.email}"


class DesignTemplate(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='design_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    product = models.CharField(max_length=100)  # Product ID as string
    design_data = models.JSONField()
    thumbnail_front = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_back = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_left = models.URLField(max_length=500, blank=True, null=True)
    thumbnail_right = models.URLField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.brand.name}"


class DesignShare(models.Model):
    """Model for shared design links (if needed for tracking)"""
    design = models.ForeignKey(Design, on_delete=models.CASCADE, related_name='shares')
    share_code = models.CharField(max_length=50, unique=True, blank=True)
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Share for {self.design.name}"
