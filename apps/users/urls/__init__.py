from django.urls import path, include

urlpatterns = [
    path('', include('apps.users.urls.user_urls')),
    path('auth/', include('apps.users.urls.auth_urls')),
    path('seller/', include('apps.users.urls.seller_urls')),
]