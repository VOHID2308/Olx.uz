"""
Autentifikatsiya URL patterns
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views.auth_views import TelegramLoginView, LogoutView

urlpatterns = [
    path('telegram-login/', TelegramLoginView.as_view(), name='telegram-login'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
]