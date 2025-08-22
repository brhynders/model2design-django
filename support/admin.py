from django.contrib import admin
from .models import SupportSubmission, FAQ, Tutorial


@admin.register(SupportSubmission)
class SupportSubmissionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'email', 'name', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']
    search_fields = ['subject', 'email', 'name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['question', 'answer']
    ordering = ['order', '-created_at']


@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description', 'content']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order', '-created_at']
