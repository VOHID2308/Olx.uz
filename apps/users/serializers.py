"""
Users app serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SellerProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Foydalanuvchi serializer - o'z profilini ko'rish/tahrirlash"""

    full_name = serializers.ReadOnlyField()
    has_seller_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'telegram_id', 'username', 'first_name', 'last_name',
            'phone_number', 'role', 'avatar', 'is_active',
            'date_joined', 'last_login', 'full_name', 'has_seller_profile'
        ]
        read_only_fields = ['id', 'telegram_id', 'username', 'role', 'is_active', 'date_joined', 'last_login']

    def get_has_seller_profile(self, obj):
        return hasattr(obj, 'seller_profile')


class UserUpdateSerializer(serializers.ModelSerializer):
    """Foydalanuvchi profilini tahrirlash serializer"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'avatar']


class TelegramLoginSerializer(serializers.Serializer):

    telegram_id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True)
    photo_url = serializers.CharField(required=False, allow_blank=True)

class SellerProfileSerializer(serializers.ModelSerializer):
    """Sotuvchi profili serializer"""

    user = UserSerializer(read_only=True)
    rating = serializers.FloatField(read_only=True)
    total_sales = serializers.IntegerField(read_only=True)

    class Meta:
        model = SellerProfile
        fields = [
            'id', 'user', 'shop_name', 'shop_description', 'shop_logo',
            'region', 'district', 'address', 'rating', 'total_sales',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'rating', 'total_sales']


class SellerProfileCreateSerializer(serializers.ModelSerializer):
    """Sotuvchi profili yaratish serializer"""

    class Meta:
        model = SellerProfile
        fields = ['shop_name', 'shop_description', 'shop_logo', 'region', 'district', 'address']

    def validate(self, attrs):
        user = self.context['request'].user
        if hasattr(user, 'seller_profile'):
            raise serializers.ValidationError("Siz allaqachon sotuvchi profiliga egasiz.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        seller_profile = SellerProfile.objects.create(user=user, **validated_data)
        # Rolni seller ga o'zgartirish
        user.role = 'seller'
        user.save(update_fields=['role'])
        return seller_profile


class PublicSellerSerializer(serializers.ModelSerializer):
    """Sotuvchi haqida public ma'lumot"""

    full_name = serializers.CharField(source='user.full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = SellerProfile
        fields = [
            'id', 'full_name', 'username', 'avatar',
            'shop_name', 'shop_description', 'shop_logo',
            'region', 'district', 'rating', 'total_sales', 'created_at'
        ]