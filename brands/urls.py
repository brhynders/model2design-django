from django.urls import path
from . import views

app_name = 'brands'

urlpatterns = [
    # Brand management dashboard
    path('dashboard/', views.brand_dashboard, name='dashboard'),
    
    # Brand switching
    path('switch/<slug:brand_slug>/', views.switch_brand, name='switch_brand'),
    
    # Brand catalog
    path('catalog/', views.BrandCatalogView.as_view(), name='catalog'),
    
    # Brand templates
    path('templates/', views.BrandTemplateListView.as_view(), name='templates'),
    
    # Brand images
    path('images/', views.BrandImageListView.as_view(), name='images'),
    path('image-categories/', views.BrandImageCategoryListView.as_view(), name='image_categories'),
    
    # Brand settings
    path('settings/', views.brand_settings, name='settings'),
    path('settings/<slug:brand_slug>/', views.brand_settings, name='settings_brand'),
    
    # Brand earnings
    path('earnings/', views.BrandEarningsListView.as_view(), name='earnings'),
    
    # API endpoints for AJAX/JavaScript
    path('api/templates/', views.api_brand_templates, name='api_templates'),
    path('api/public-templates/', views.api_public_templates, name='api_public_templates'),
    path('api/backgrounds/', views.api_brand_backgrounds, name='api_backgrounds'),
]