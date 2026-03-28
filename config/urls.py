"""
OLX.UZ - Asosiy URL konfiguratsiyasi
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.http import HttpResponse


def home(request):
    return HttpResponse("Welcome to OLX clone!")

urlpatterns = [
    path('', TemplateView.as_view(
    template_name="miniapp/index.html"
)),
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls.auth_urls')),
    path('miniapp/', TemplateView.as_view(template_name="miniapp/index.html")),
    path('api/v1/users/',      include('apps.users.urls.user_urls')),
    path('api/v1/sellers/',    include('apps.users.urls.seller_urls')),
    path('api/v1/categories/', include('apps.categories.urls')),
    path('api/v1/products/',   include('apps.products.urls')),
    path('api/v1/favorites/',  include('apps.products.favorite_urls')),
    path('api/v1/orders/',     include('apps.orders.urls')),
    path('api/v1/reviews/',    include('apps.reviews.urls')),

    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',  SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)