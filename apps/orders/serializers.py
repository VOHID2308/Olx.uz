"""
Orders app serializers
"""

from rest_framework import serializers
from .models import Order
from apps.products.serializers import ProductListSerializer


class OrderSerializer(serializers.ModelSerializer):
    """Buyurtma to'liq ma'lumotlari"""

    product = ProductListSerializer(read_only=True)
    buyer_name = serializers.CharField(source='buyer.full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.full_name', read_only=True)
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'product', 'buyer', 'buyer_name', 'seller', 'seller_name',
            'final_price', 'status', 'meeting_location', 'meeting_time',
            'notes', 'has_review', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'buyer', 'seller', 'created_at', 'updated_at']

    def get_has_review(self, obj):
        return hasattr(obj, 'review')


class OrderCreateSerializer(serializers.ModelSerializer):
    """Yangi buyurtma yaratish"""

    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = ['product_id', 'notes']

    def validate_product_id(self, value):
        from apps.products.models import Product
        try:
            product = Product.objects.get(id=value, status='aktiv')
        except Product.DoesNotExist:
            raise serializers.ValidationError("Bu mahsulot topilmadi yoki aktiv emas.")
        return value

    def validate(self, attrs):
        from apps.products.models import Product
        user = self.context['request'].user
        product = Product.objects.get(id=attrs['product_id'])

        # O'z mahsulotiga buyurtma bera olmaydi
        if product.seller == user:
            raise serializers.ValidationError("O'z mahsulotingizga buyurtma bera olmaysiz.")

        attrs['product'] = product
        return attrs

    def create(self, validated_data):
        from apps.products.models import Product
        user = self.context['request'].user
        product = validated_data.pop('product')
        validated_data.pop('product_id', None)

        order = Order.objects.create(
            buyer=user,
            seller=product.seller,
            product=product,
            final_price=product.price,
            **validated_data
        )
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Buyurtma statusini yangilash"""

    class Meta:
        model = Order
        fields = ['status', 'meeting_location', 'meeting_time', 'final_price']

    def validate(self, attrs):
        user = self.context['request'].user
        order = self.instance
        new_status = attrs.get('status', order.status)

        # Status o'tish qoidalari
        if user == order.seller:
            # Sotuvchi faqat: kutilyapti -> kelishilgan | bekor qilingan
            allowed = {
                'kutilyapti': ['kelishilgan', 'bekor qilingan']
            }
            current_allowed = allowed.get(order.status, [])
            if new_status not in current_allowed and new_status != order.status:
                raise serializers.ValidationError(
                    f"Sotuvchi bu statusga o'zgartira olmaydi: {new_status}"
                )

        elif user == order.buyer:
            # Xaridor faqat: kelishilgan -> sotib olingan | bekor qilingan
            allowed = {
                'kelishilgan': ['sotib olingan', 'bekor qilingan']
            }
            current_allowed = allowed.get(order.status, [])
            if new_status not in current_allowed and new_status != order.status:
                raise serializers.ValidationError(
                    f"Xaridor bu statusga o'zgartira olmaydi: {new_status}"
                )
        else:
            raise serializers.ValidationError("Bu buyurtmaga ruxsatingiz yo'q.")

        return attrs

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if new_status == 'sotib olingan':
            instance.complete_purchase()
        else:
            instance.save()

        return instance