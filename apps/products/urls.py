from django.urls import path
from .views import (
    ProductListCreateView, ProductDetailView,
    ProductPublishView, ProductArchiveView, ProductSoldView
)

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/publish/', ProductPublishView.as_view(), name='product-publish'),
    path('<int:pk>/archive/', ProductArchiveView.as_view(), name='product-archive'),
    path('<int:pk>/sold/', ProductSoldView.as_view(), name='product-sold'),
]