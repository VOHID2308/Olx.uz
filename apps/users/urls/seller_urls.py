"""
Seller URL patterns
"""

from django.urls import path
from apps.users.views.user_views import PublicSellerDetailView, SellerProductsView

urlpatterns = [
    path('<int:seller_id>/', PublicSellerDetailView.as_view(), name='seller-detail'),
    path('<int:seller_id>/products/', SellerProductsView.as_view(), name='seller-products'),
]