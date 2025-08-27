from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from brands.models import Brand
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
import os

User = get_user_model()


def design_thumbnail_upload_path(instance, filename):
    """Generate upload path for design thumbnails"""
    # Use user_id if available, otherwise session_id
    user_folder = f"user_{instance.user.id}" if instance.user else f"session_{instance.session_id}"
    return f"design_thumbnails/{user_folder}/{filename}"


class Design(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='designs',
        null=True,
        blank=True,
        help_text="User who created the design (null for guest users)"
    )
    session_id = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text="Session ID for guest users"
    )
    name = models.CharField(max_length=255)
    product = models.IntegerField()  # References product ID from data.products.php
    data = models.JSONField()  # Stores the design data
    thumbnail_front = models.ImageField(upload_to=design_thumbnail_upload_path, blank=True, null=True)
    thumbnail_back = models.ImageField(upload_to=design_thumbnail_upload_path, blank=True, null=True)
    thumbnail_left = models.ImageField(upload_to=design_thumbnail_upload_path, blank=True, null=True)
    thumbnail_right = models.ImageField(upload_to=design_thumbnail_upload_path, blank=True, null=True)
    public = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        # Remove brand from unique constraint since we removed brand field
        unique_together = []

    def __str__(self):
        if self.user:
            return f"{self.name} - {self.user.email}"
        return f"{self.name} - Guest ({self.session_id[:8]}...)"
    
    def get_owner_display(self):
        """Get display name for the design owner"""
        if self.user:
            return self.user.get_full_name() or self.user.email
        return f"Guest User"


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


def design_image_upload_path(instance, filename):
    """Generate upload path for design images"""
    # Use user_id if available, otherwise session_id
    user_folder = f"user_{instance.user.id}" if instance.user else f"session_{instance.session_id}"
    return f"design_images/{user_folder}/{filename}"


class DesignImage(models.Model):
    """User-uploaded images for use in designs"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='design_images',
        null=True,
        blank=True,
        help_text="User who uploaded the image (null for guest users)"
    )
    session_id = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text="Session ID for guest users"
    )
    image = models.ImageField(
        upload_to=design_image_upload_path,
        help_text="Original uploaded image"
    )
    thumbnail = ImageSpecField(
        source='image',
        processors=[ResizeToFill(100, 100)],
        format='JPEG',
        options={'quality': 85}
    )
    name = models.CharField(
        max_length=255,
        help_text="Display name for the image"
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Image width in pixels"
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Image height in pixels"
    )
    filetype = models.CharField(
        max_length=10,
        blank=True,
        help_text="File extension/type (jpg, png, etc.)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_id})"
        return f"{self.name} - {owner}"

    def save(self, *args, **kwargs):
        # Extract metadata from the image
        if self.image:
            self.file_size = self.image.size
            
            # Get image dimensions
            from PIL import Image
            img = Image.open(self.image)
            self.width, self.height = img.size
            
            # Extract file extension
            self.filetype = os.path.splitext(self.image.name)[1].lower().lstrip('.')
            
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        # Ensure either user or session_id is provided, but not both
        if self.user and self.session_id:
            raise ValidationError("Image cannot have both user and session_id")
        if not self.user and not self.session_id:
            raise ValidationError("Image must have either user or session_id")
