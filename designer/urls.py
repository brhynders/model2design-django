from django.urls import path
from . import views

app_name = 'designer'

urlpatterns = [
    path('', views.designer_view, name='designer'),
    path('save/', views.save_design, name='save_design'),
    path('update-visibility/<int:design_id>/', views.update_design_visibility, name='update_design_visibility'),
    path('delete/<int:design_id>/', views.delete_design, name='delete_design'),
    path('share/<int:design_id>/', views.design_share, name='design_share'),
    path('copy/<int:design_id>/', views.copy_design, name='copy_design'),
    path('my-designs/', views.my_designs, name='my_designs'),
    
    # Template related URLs
    path('templates/', views.select_template, name='select_template'),
    path('template/<int:template_id>/load/', views.load_template, name='load_template'),
    path('template/<int:template_id>/edit/', views.edit_template, name='edit_template'),
    
    # Image Bank API endpoints
    path('images/', views.user_images_api, name='user_images_api'),
    path('images/upload/', views.upload_image_api, name='upload_image_api'),
    path('images/delete/<str:image_id>/', views.delete_image_api, name='delete_image_api'),
]