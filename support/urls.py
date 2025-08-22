from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('', views.SupportView.as_view(), name='support'),
    path('submit/', views.SupportSubmitView.as_view(), name='submit'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', views.TermsOfServiceView.as_view(), name='terms_of_service'),
    path('return-policy/', views.ReturnPolicyView.as_view(), name='return_policy'),
    path('shipping-info/', views.ShippingInfoView.as_view(), name='shipping_info'),
    path('tutorials/', views.TutorialsView.as_view(), name='tutorials'),
    path('tutorials/<slug:slug>/', views.TutorialDetailView.as_view(), name='tutorial_detail'),
]