from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'buyer', 'seller', 'final_price', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['buyer__username', 'seller__username', 'product__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']