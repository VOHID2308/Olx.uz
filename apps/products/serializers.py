"""
Products app serializers
"""

from rest_framework import serializers
from .models import Product, ProductImage, Favorite


class ProductImageSerializer(serializers.ModelSerializer):
    """Mahsulot rasmi serializer"""

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'order', 'is_main', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Mahsulotlar ro'yxati uchun qisqa serializer"""

    main_image = serializers.SerializerMethodField()
    seller_name = serializers.CharField(source='seller.full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'price', 'price_type', 'condition',
            'region', 'district', 'status', 'view_count', 'favorite_count',
            'seller_name', 'category_name', 'main_image', 'created_at'
        ]

    def get_main_image(self, obj):
        main = obj.images.filter(is_main=True).first()
        if main:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main.image.url)
            return main.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Mahsulot to'liq ma'lumotlari"""

    images = ProductImageSerializer(many=True, read_only=True)
    seller_info = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'condition', 'price', 'price_type',
            'region', 'district', 'status', 'view_count', 'favorite_count',
            'category', 'category_name', 'category_slug',
            'seller_info', 'images',
            'created_at', 'updated_at', 'published_at', 'expires_at'
        ]

    def get_seller_info(self, obj):
        seller = obj.seller
        data = {
            'id': seller.id,
            'full_name': seller.full_name,
            'username': seller.username,
        }
        if hasattr(seller, 'seller_profile'):
            data['seller_profile_id'] = seller.seller_profile.id
            data['shop_name'] = seller.seller_profile.shop_name
            data['rating'] = seller.seller_profile.rating
        return data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Mahsulot yaratish/tahrirlash serializer"""

    class Meta:
        model = Product
        fields = [
            'title', 'description', 'condition', 'price', 'price_type',
            'category', 'region', 'district'
        ]

    def validate(self, attrs):
        # Faqat seller role o'z e'lonini qo'sha oladi
        user = self.context['request'].user
        if user.role != 'seller':
            raise serializers.ValidationError("Faqat sotuvchilar e'lon qo'sha oladi.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return Product.objects.create(seller=user, **validated_data)

    def update(self, instance, validated_data):
        """Tahrirlangandan keyin moderatsiyada statusiga qaytarish"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if instance.status == 'aktiv':
            instance.status = 'moderatsiyada'
        instance.save()
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    """Sevimlilar serializer"""

    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(status='aktiv'),
        write_only=True,
        source='product'
    )

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'product_id', 'created_at']

    def validate(self, attrs):
        user = self.context['request'].user
        product = attrs['product']
        if Favorite.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("Bu mahsulot allaqachon sevimlilarda bor.")
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return Favorite.objects.create(user=user, **validated_data)