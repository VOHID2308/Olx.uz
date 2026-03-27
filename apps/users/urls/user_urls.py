"""
User URL patterns
"""

from django.urls import path
from apps.users.views.user_views import MeView, UpgradeToSellerView

urlpatterns = [
    path('me/', MeView.as_view(), name='user-me'),
    path('me/upgrade-to-seller/', UpgradeToSellerView.as_view(), name='upgrade-to-seller'),
]