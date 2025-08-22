from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('<slug:category_slug>/', views.product_list_by_category, name='category'),
    path('product/<int:pk>/', views.product_detail, name='detail'),
]