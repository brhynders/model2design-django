from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Extended User model with additional fields"""
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_brand_owner = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for compatibility with PHP app
    name = models.CharField(max_length=255, blank=True)
    
    def save(self, *args, **kwargs):
        # Sync name with first_name + last_name
        if self.name and not (self.first_name and self.last_name):
            # If name is provided but first/last names are empty, split the name
            parts = self.name.split(' ', 1)
            self.first_name = parts[0]
            if len(parts) > 1:
                self.last_name = parts[1]
        elif not self.name and (self.first_name or self.last_name):
            # If name is empty but first/last names exist, combine them
            self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'user'
        
        
class PasswordResetToken(models.Model):
    """Password reset tokens for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_token'
