from django.contrib import admin
from .models import License, Activation
from .models import License, Activation, Device

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("key", "customer_id", "max_activations", "expires_at", "is_revoked", "created_at")
    search_fields = ("key", "customer_id")
    list_filter = ("is_revoked",)

@admin.register(Activation)
class ActivationAdmin(admin.ModelAdmin):
    list_display = ("license", "fingerprint", "created_at", "last_seen_at")
    search_fields = ("fingerprint", "license__key")

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("serial", "license", "revoked", "created_at")
    list_filter = ("revoked", "license")
    search_fields = ("serial", "license__key")
    actions = ["revoke_devices"]

    @admin.action(description="Revogar dispositivos selecionados")
    def revoke_devices(self, request, queryset):
        queryset.update(revoked=True)