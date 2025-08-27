from django.urls import path
from . import views

app_name = 'designer'

urlpatterns = [
    path('', views.designer_view, name='designer'),
    path('save/', views.save_design, name='save_design'),
    path('share/<int:design_id>/', views.design_share, name='design_share'),
    path('my-designs/', views.my_designs, name='my_designs'),
    path('select-template/', views.select_template, name='select_template'),
    
    # Image Bank API endpoints
    path('images/', views.user_images_api, name='user_images_api'),
    path('images/upload/', views.upload_image_api, name='upload_image_api'),
    path('images/delete/<str:image_id>/', views.delete_image_api, name='delete_image_api'),
]