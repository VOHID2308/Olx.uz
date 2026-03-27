"""
Orders app views
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer, OrderStatusUpdateSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET: O'z buyurtmalarini ko'rish (buyer yoki seller sifatida)
    POST: Yangi buyurtma yaratish
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = self.request.query_params.get('role', None)

        if role == 'buyer':
            return Order.objects.filter(buyer=user)
        elif role == 'seller':
            return Order.objects.filter(seller=user)
        else:
            # Ikkala rolda ham ko'rinadi
            return Order.objects.filter(
                Q(buyer=user) | Q(seller=user)
            ).select_related('product', 'buyer', 'seller').prefetch_related('product__images')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter('role', OpenApiTypes.STR, description='buyer yoki seller sifatida filterlash'),
        ],
        summary="Buyurtmalar ro'yxati",
        tags=['Orders']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Yangi buyurtma yaratish", tags=['Orders'])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """
    GET: Bitta buyurtma (faqat buyer yoki seller)
    PATCH: Statusni yangilash
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('product', 'buyer', 'seller').prefetch_related('product__images')

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return OrderStatusUpdateSerializer
        return OrderSerializer

    @extend_schema(summary="Bitta buyurtma", tags=['Orders'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="Buyurtma statusini yangilash", tags=['Orders'])
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)