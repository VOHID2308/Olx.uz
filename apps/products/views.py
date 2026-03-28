"""
Products app views - mahsulotlar CRUD va action larlar
"""

from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Product, Favorite
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, FavoriteSerializer
)
from .filters import ProductFilter
from apps.users.permissions import IsSeller, IsProductOwner


class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET: Barcha aktiv mahsulotlar (filter, search, pagination)
    POST: Yangi e'lon yaratish (faqat seller)
    """

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'view_count', 'favorite_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return Product.objects.filter(
            status='aktiv'
        ).select_related('seller', 'category').prefetch_related('images')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsSeller()]
        return [AllowAny()]

    @extend_schema(
        parameters=[
            OpenApiParameter('category', OpenApiTypes.STR, description='Kategoriya slug yoki id'),
            OpenApiParameter('region', OpenApiTypes.STR, description='Viloyat'),
            OpenApiParameter('min_price', OpenApiTypes.FLOAT, description='Minimal narx'),
            OpenApiParameter('max_price', OpenApiTypes.FLOAT, description='Maksimal narx'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Qidiruv (sarlavha, tavsif)'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Tartiblash (created_at, price, -view_count)'),
        ],
        summary="Mahsulotlar ro'yxati",
        tags=['Products']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Yangi e'lon yaratish", tags=['Products'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Bitta mahsulot (view_count +1)
    PUT/PATCH: Tahrirlash (faqat egasi)
    DELETE: O'chirish (faqat egasi)
    """

    def get_queryset(self):
        return Product.objects.all().select_related('seller', 'category').prefetch_related('images')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsProductOwner()]
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """Ko'rilganda view_count ni oshirish"""
        instance = self.get_object()
        if instance.status != 'aktiv' and (not request.user.is_authenticated or instance.seller != request.user):
            return Response(
                {'error': 'Mahsulot topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        # view_count oshirish
        Product.objects.filter(pk=instance.pk).update(view_count=instance.view_count + 1)
        instance.view_count += 1
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="Bitta mahsulot", tags=['Products'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Mahsulotni tahrirlash", tags=['Products'])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary="Mahsulotni o'chirish", tags=['Products'])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class ProductPublishView(APIView):
    """E'lonni aktiv qilish (moderatsiyadan o'tkazish)"""

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(summary="E'lonni nashr qilish", tags=['Products'])
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, seller=request.user)
        except Product.DoesNotExist:
            return Response({'error': 'Mahsulot topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if product.status not in ['moderatsiyada', 'rad etilgan']:
            return Response(
                {'error': f'Bu mahsulot allaqachon {product.status} statusida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.publish()
        return Response({'message': 'Mahsulot muvaffaqiyatli nashr qilindi', 'status': product.status})


class ProductArchiveView(APIView):
    """E'lonni arxivlash"""

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(summary="E'lonni arxivlash", tags=['Products'])
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, seller=request.user)
        except Product.DoesNotExist:
            return Response({'error': 'Mahsulot topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        product.archive()
        return Response({'message': 'Mahsulot arxivlandi', 'status': product.status})


class ProductSoldView(APIView):
    """E'lonni sotilgan deb belgilash"""

    permission_classes = [IsAuthenticated, IsSeller]

    @extend_schema(summary="Mahsulotni sotilgan deb belgilash", tags=['Products'])
    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, seller=request.user)
        except Product.DoesNotExist:
            return Response({'error': 'Mahsulot topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if product.status == 'sotilgan':
            return Response({'error': 'Mahsulot allaqachon sotilgan'}, status=status.HTTP_400_BAD_REQUEST)

        product.mark_as_sold()
        return Response({'message': 'Mahsulot sotilgan deb belgilandi', 'status': product.status})


# ---- FAVORITES ----

class FavoriteListCreateView(generics.ListCreateAPIView):
    """
    GET: O'z sevimlilari ro'yxati
    POST: Sevimlilarga qo'shish
    """

    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('product__seller', 'product__category').prefetch_related('product__images')

    @extend_schema(summary="Sevimlilar ro'yxati", tags=['Favorites'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Sevimlilarga qo'shish", tags=['Favorites'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class FavoriteDeleteView(generics.DestroyAPIView):
    """Sevimlilardan olib tashlash"""

    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    @extend_schema(summary="Sevimlilardan olib tashlash", tags=['Favorites'])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)