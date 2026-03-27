"""
Reviews app serializers
"""

from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Fikr to'liq ma'lumotlari"""

    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.full_name', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'order_id', 'reviewer', 'reviewer_name',
            'seller', 'seller_name', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'seller', 'created_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Yangi fikr qoldirish"""

    order_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Review
        fields = ['order_id', 'rating', 'comment']

    def validate_order_id(self, value):
        from apps.orders.models import Order
        user = self.context['request'].user
        try:
            order = Order.objects.get(id=value, buyer=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Bu buyurtma topilmadi.")

        if order.status != 'sotib olingan':
            raise serializers.ValidationError(
                "Faqat 'sotib olingan' buyurtmalar uchun fikr qoldirish mumkin."
            )

        if hasattr(order, 'review'):
            raise serializers.ValidationError(
                "Bu buyurtma uchun fikr allaqachon qoldirilgan."
            )

        return value

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Reyting 1 dan 5 gacha bo'lishi kerak.")
        return value

    def create(self, validated_data):
        from apps.orders.models import Order
        user = self.context['request'].user
        order_id = validated_data.pop('order_id')
        order = Order.objects.get(id=order_id)

        review = Review.objects.create(
            order=order,
            reviewer=user,
            seller=order.seller,
            **validated_data
        )
        return review