from django.urls import path
from . import views
from django.http import HttpResponse

def test(request):
    return HttpResponse("Users working")

urlpatterns = [
    path('test/', test),
]