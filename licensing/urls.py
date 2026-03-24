from django.urls import path
from .views import activate, validate_license, health

urlpatterns = [
    path("activate/", activate),
    path("validate-license/", validate_license),
    path("health", health),
]