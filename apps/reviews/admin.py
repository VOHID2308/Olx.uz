from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'reviewer', 'seller', 'rating', 'order', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__username', 'seller__username', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['created_at']