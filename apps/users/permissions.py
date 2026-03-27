"""
Custom permission classlar
"""

from rest_framework import permissions


class IsSeller(permissions.BasePermission):
    """Faqat Seller roli uchun ruxsat"""

    message = "Bu amalni faqat sotuvchilar bajarishi mumkin."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'seller'
        )


class IsCustomer(permissions.BasePermission):
    """Faqat Customer roli uchun ruxsat"""

    message = "Bu amalni faqat xaridorlar bajarishi mumkin."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'customer'
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Faqat egasi o'zgartira oladi, boshqalar faqat o'qiy oladi"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsProductOwner(permissions.BasePermission):
    """Faqat mahsulot egasi (seller) o'zgartira oladi"""

    def has_object_permission(self, request, view, obj):
        return obj.seller == request.user