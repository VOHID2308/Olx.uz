from django.contrib import admin
from .models import Product, ProductImage, Favorite


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'price', 'status', 'view_count', 'created_at']
    list_filter = ['status', 'condition', 'price_type', 'region']
    search_fields = ['title', 'description', 'seller__username']
    ordering = ['-created_at']
    inlines = [ProductImageInline]
    list_editable = ['status']
    readonly_fields = ['view_count', 'favorite_count', 'created_at', 'updated_at']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'order', 'is_main', 'created_at']
    list_filter = ['is_main']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__username', 'product__title']