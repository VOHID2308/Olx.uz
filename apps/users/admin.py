from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SellerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['telegram_id', 'username', 'full_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active']
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('telegram_id', 'username', 'password')}),
        ('Shaxsiy ma\'lumotlar', {'fields': ('first_name', 'last_name', 'phone_number', 'avatar')}),
        ('Ruxsatlar', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Muhim sanalar', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telegram_id', 'username', 'first_name', 'role'),
        }),
    )


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'user', 'region', 'rating', 'total_sales', 'created_at']
    list_filter = ['region']
    search_fields = ['shop_name', 'user__username', 'user__first_name']
    ordering = ['-rating']