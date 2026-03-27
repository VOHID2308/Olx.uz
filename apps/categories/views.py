"""
Kategoriya views
"""

from rest_framework import generics
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .models import Category
from .serializers import CategorySerializer, CategoryDetailSerializer
from apps.products.serializers import ProductListSerializer


class CategoryListView(generics.ListAPIView):
    """
    Barcha aktiv asosiy kategoriyalar ro'yxati (children bilan)
    """

    permission_classes = [AllowAny]
    serializer_class = CategorySerializer

    def get_queryset(self):
        # Faqat asosiy kategoriyalar (parent yo'q)
        return Category.objects.filter(
            is_active=True,
            parent=None
        ).prefetch_related('children')

    @extend_schema(summary="Kategoriyalar ro'yxati", tags=['Categories'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CategoryDetailView(generics.RetrieveAPIView):
    """
    Bitta kategoriya detallari (slug orqali)
    """

    permission_classes = [AllowAny]
    serializer_class = CategoryDetailSerializer
    lookup_field = 'slug'
    queryset = Category.objects.filter(is_active=True).prefetch_related('children')

    @extend_schema(summary="Bitta kategoriya", tags=['Categories'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CategoryProductsView(generics.ListAPIView):
    """
    Kategoriya bo'yicha aktiv mahsulotlar
    """

    permission_classes = [AllowAny]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        from apps.products.models import Product
        slug = self.kwargs.get('slug')
        try:
            category = Category.objects.get(slug=slug, is_active=True)
            # Shu kategoriya va barcha sub-kategoriyalar
            category_ids = self._get_category_ids(category)
            return Product.objects.filter(
                category__in=category_ids,
                status='aktiv'
            ).select_related('seller', 'category').prefetch_related('images')
        except Category.DoesNotExist:
            from apps.products.models import Product
            return Product.objects.none()

    def _get_category_ids(self, category):
        """Kategoriya va barcha bolalar ID larini olish"""
        ids = [category.id]
        for child in category.children.filter(is_active=True):
            ids.extend(self._get_category_ids(child))
        return ids

    @extend_schema(summary="Kategoriya mahsulotlari", tags=['Categories'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)