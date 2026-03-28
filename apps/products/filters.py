"""
Products filterlash - django-filter orqali
"""

import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Mahsulotlar uchun filter.
    Quyidagi parameterlar bo'yicha filterlash mumkin:
    - category (slug yoki id)
    - region
    - min_price, max_price
    - search (title va description)
    - ordering
    """

    category = django_filters.CharFilter(method='filter_category')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    region = django_filters.CharFilter(field_name='region', lookup_expr='icontains')
    condition = django_filters.CharFilter(field_name='condition', lookup_expr='exact')
    price_type = django_filters.CharFilter(field_name='price_type', lookup_expr='exact')

    class Meta:
        model = Product
        fields = ['category', 'region', 'min_price', 'max_price', 'condition', 'price_type']

    def filter_category(self, queryset, name, value):
        """Kategoriya bo'yicha filterlash (slug yoki id)"""
        from apps.categories.models import Category
        try:
            category_id = int(value)
            category = Category.objects.get(id=category_id)
        except (ValueError, Category.DoesNotExist):
            try:
                category = Category.objects.get(slug=value)
            except Category.DoesNotExist:
                return queryset.none()

        category_ids = self._get_category_ids(category)
        return queryset.filter(category__in=category_ids)

    def _get_category_ids(self, category):
        """Kategoriya va barcha bolalar ID larini olish"""
        ids = [category.id]
        for child in category.children.filter(is_active=True):
            ids.extend(self._get_category_ids(child))
        return ids