"""
Kategoriya serializers
"""

from rest_framework import serializers
from .models import Category


class CategoryChildSerializer(serializers.ModelSerializer):
    """Child kategoriya (ichki)"""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'order_num']


class CategorySerializer(serializers.ModelSerializer):
    """Kategoriya serializer - children bilan"""

    children = CategoryChildSerializer(many=True, read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'icon',
            'description', 'is_active', 'order_num',
            'created_at', 'children', 'products_count'
        ]

    def get_products_count(self, obj):
        return obj.products.filter(status='aktiv').count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Bitta kategoriya uchun to'liq ma'lumot"""

    children = CategoryChildSerializer(many=True, read_only=True)
    parent_info = CategoryChildSerializer(source='parent', read_only=True)
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'parent', 'parent_info',
            'icon', 'description', 'is_active', 'order_num',
            'created_at', 'children', 'products_count'
        ]

    def get_products_count(self, obj):
        return obj.get_all_products_count()