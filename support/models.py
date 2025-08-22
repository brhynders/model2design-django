from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SupportSubmission(models.Model):
    CATEGORY_CHOICES = [
        ('orders', 'Orders'),
        ('account', 'Account'),
        ('designing', 'Designing'),
        ('request_model', 'Request Model'),
        ('website', 'Website Problem'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    additional_data = models.JSONField(blank=True, null=True)  # Store extra form fields
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.subject} - {self.email}"


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        
    def __str__(self):
        return self.question


class Tutorial(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content = models.TextField()
    slug = models.SlugField(unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        
    def __str__(self):
        return self.title
