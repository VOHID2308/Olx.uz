"""
Reviews app views
"""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET: Barcha fikrlar (seller_id bo'yicha filterlash mumkin)
    POST: Fikr qoldirish (faqat autentifikatsiya qilingan)
    """

    def get_queryset(self):
        queryset = Review.objects.select_related('reviewer', 'seller', 'order')
        seller_id = self.request.query_params.get('seller_id')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(
        parameters=[
            OpenApiParameter('seller_id', OpenApiTypes.INT, description='Sotuvchi ID bo\'yicha filterlash'),
        ],
        summary="Fikrlar ro'yxati",
        tags=['Reviews']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Fikr qoldirish", tags=['Reviews'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)