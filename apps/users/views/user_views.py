"""
User va SellerProfile views
"""

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema

from apps.users.serializers import (
    UserSerializer, UserUpdateSerializer,
    SellerProfileCreateSerializer, SellerProfileSerializer,
    PublicSellerSerializer
)
from apps.users.models import SellerProfile

User = get_user_model()


class MeView(APIView):
    """
    O'z profilini ko'rish va tahrirlash
    GET: profilni ko'rish
    PATCH: profilni yangilash
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer, summary="O'z profilini ko'rish", tags=['Users'])
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=UserUpdateSerializer,
        responses=UserSerializer,
        summary="Profilni yangilash",
        tags=['Users']
    )
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class UpgradeToSellerView(APIView):
    """
    Customer dan Seller ga o'tish.
    SellerProfile yaratadi va rolni o'zgartiradi.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SellerProfileCreateSerializer,
        responses=SellerProfileSerializer,
        summary="Sotuvchi bo'lish",
        tags=['Users']
    )
    def post(self, request):
        if request.user.role == 'seller':
            return Response(
                {'error': 'Siz allaqachon sotuvchisiz'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SellerProfileCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        seller_profile = serializer.save()

        return Response(
            SellerProfileSerializer(seller_profile).data,
            status=status.HTTP_201_CREATED
        )


class PublicSellerDetailView(APIView):
    """
    Sotuvchi haqida public ma'lumot
    """

    permission_classes = [AllowAny]

    @extend_schema(responses=PublicSellerSerializer, summary="Sotuvchi ma'lumotlari", tags=['Sellers'])
    def get(self, request, seller_id):
        try:
            seller_profile = SellerProfile.objects.select_related('user').get(id=seller_id)
        except SellerProfile.DoesNotExist:
            return Response({'error': 'Sotuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicSellerSerializer(seller_profile)
        return Response(serializer.data)


class SellerProductsView(generics.ListAPIView):
    """
    Sotuvchining barcha aktiv mahsulotlari
    """

    permission_classes = [AllowAny]

    def get_queryset(self):
        from apps.products.models import Product
        seller_id = self.kwargs.get('seller_id')
        try:
            seller_profile = SellerProfile.objects.get(id=seller_id)
            return Product.objects.filter(
                seller=seller_profile.user,
                status='aktiv'
            ).prefetch_related('images')
        except SellerProfile.DoesNotExist:
            return Product.objects.none()

    def get_serializer_class(self):
        from apps.products.serializers import ProductListSerializer
        return ProductListSerializer