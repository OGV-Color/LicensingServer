from django.urls import path

from . import views
from .views import activate, validate_license, health, deactivate, validate_device

urlpatterns = [
    path("activate/", activate),
    path("validate-license/", validate_license),
    path("deactivate/", deactivate),
    path("health/", health),
    path("validate-device/", views.validate_device),
]