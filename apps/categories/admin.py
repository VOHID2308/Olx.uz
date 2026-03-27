from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'is_active', 'order_num', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order_num', 'name']
    list_editable = ['is_active', 'order_num']