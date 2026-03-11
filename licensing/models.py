from django.db import models

# Create your models here.
class License(models.Model):
    key = models.CharField(max_length=64, unique=True)

    customer_id = models.CharField(max_length=64)

    max_activations = models.IntegerField(default=1)

    expires_at = models.DateTimeField(null=True, blank=True)

    is_revoked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.key} ({self.customer_id})"

class Activation(models.Model):
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name="activations")
    fingerprint = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("license", "fingerprint")

    def __str__(self) -> str:
        return f"{self.license.key} -> {self.fingerprint[:12]}..."