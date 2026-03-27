from django.urls import path
from .views import FavoriteListCreateView, FavoriteDeleteView

urlpatterns = [
    path('', FavoriteListCreateView.as_view(), name='favorite-list'),
    path('<int:pk>/', FavoriteDeleteView.as_view(), name='favorite-delete'),
]