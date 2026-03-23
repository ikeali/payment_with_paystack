from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    ProductListView,
    ProductDetailView,
    OrderListCreateView,
    OrderDetailView,
    InitiatePaymentView,
    VerifyPaymentView, PaystackCallbackView, PaystackWebhookView

)
from .views import HealthCheckView




urlpatterns = [
    # AUTH
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── PRODUCTS 
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),

    # ORDERS 
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),

    # PAYMENTS
    path('payments/initiate/<int:order_id>/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/verify/<str:reference>/', VerifyPaymentView.as_view(), name='verify-payment'),

    path('payments/callback/', PaystackCallbackView.as_view(), name='paystack-callback'),
    path('payments/webhook/', PaystackWebhookView.as_view(), name='paystack-webhook'),  # add this

    path('health/', HealthCheckView.as_view(), name='health-check'),




]