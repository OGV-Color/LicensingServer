from django.urls import path
from .views import activate, validate_license, health, deactivate

urlpatterns = [
    path("activate/", activate),
    path("validate-license/", validate_license),
    path("deactivate/", deactivate),
    path("health/", health),
]