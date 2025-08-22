from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='view'),
    path('add/', views.add_to_cart, name='add'),
    path('sidebar/', views.cart_sidebar, name='sidebar'),
]