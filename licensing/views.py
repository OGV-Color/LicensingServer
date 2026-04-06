import base64
import json
from inspect import signature

from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from .models import License, Activation

PRIVATE_KEY_PATH = getattr(settings, "LICENSE_PRIVATE_KEY_PATH", None)


def health(request):
    return JsonResponse({"status": "ok"})


def sign_payload(payload_json: str) -> str:
    with open(PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    signature_bytes = private_key.sign(
        payload_json.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )

    return base64.b64encode(signature_bytes).decode("utf-8")


@api_view(["POST"])
def activate(request):
    license_key = request.data.get("licenseKey")
    fingerprint = request.data.get("fingerprint")

    if not license_key or not fingerprint:
        return Response(
            {"detail": "licenseKey e fingerprint são obrigatórios"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        lic = License.objects.get(key=license_key)
    except License.DoesNotExist:
        return Response({"detail": "Licença inválida"}, status=status.HTTP_403_FORBIDDEN)

    if lic.is_revoked:
        return Response({"detail": "Licença revogada"}, status=status.HTTP_403_FORBIDDEN)

    if lic.expires_at and lic.expires_at < timezone.now():
        return Response({"detail": "Licença expirada"}, status=status.HTTP_403_FORBIDDEN)

    # ✅ NOVO: Verificar se já foi ativada em outro computador
    existing_activation = Activation.objects.filter(license=lic).first()

    if existing_activation:
        if existing_activation.fingerprint != fingerprint:
            # ❌ Licença já ativada em outro computador
            return Response(
                {
                    "detail": "Licença já foi ativada em outro computador",
                    "reason": "license_already_activated"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        # ✅ Mesmo computador, apenas atualiza last_seen_at
        existing_activation.last_seen_at = timezone.now()
        existing_activation.save(update_fields=["last_seen_at"])
        act = existing_activation
    else:
        # ✅ Primeira ativação
        act = Activation.objects.create(license=lic, fingerprint=fingerprint)
        act.last_seen_at = timezone.now()
        act.save(update_fields=["last_seen_at"])

    payload = {
        "app": "OGVColorCatcher",
        "customerId": lic.customer_id,
        "licenseKeyId": f"LIC_{lic.id}",
        "fingerprint": fingerprint,
        "expiresAt": (lic.expires_at.isoformat().replace("+00:00", "Z") if lic.expires_at else None),
        "features": ["PRO"],
        "issuedAt": timezone.now().isoformat().replace("+00:00", "Z"),
    }

    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    signature_b64 = sign_payload(payload_json)

    return Response({"payload": payload_json, "signature": signature_b64})


@api_view(["POST"])
def validate_license(request):
    license_key_id = request.data.get("licenseKeyId")
    fingerprint = request.data.get("fingerprint")

    def now_z():
        return timezone.now().isoformat().replace("+00:00", "Z")

    if not license_key_id or not fingerprint:
        return Response({"valid": False, "reason": "missing_data", "serverUtc": now_z()}, status=400)

    if not str(license_key_id).startswith("LIC_"):
        return Response({"valid": False, "reason": "invalid_license_id", "serverUtc": now_z()}, status=400)

    try:
        license_id = int(str(license_key_id).replace("LIC_", ""))
        lic = License.objects.get(id=license_id)
    except (ValueError, License.DoesNotExist):
        return Response({"valid": False, "reason": "not_found", "serverUtc": now_z()}, status=404)

    if lic.is_revoked:
        return Response({"valid": False, "reason": "revoked", "serverUtc": now_z()})

    if lic.expires_at and lic.expires_at < timezone.now():
        return Response({"valid": False, "reason": "expired", "serverUtc": now_z()})

    # ✅ NOVO: Verificar se fingerprint bate
    exists = Activation.objects.filter(license=lic, fingerprint=fingerprint).exists()
    if not exists:
        return Response({"valid": False, "reason": "fingerprint_mismatch", "serverUtc": now_z()})

    return Response({"valid": True, "serverUtc": now_z()})


@api_view(["POST"])
def deactivate(request):
    """Desativa uma licença para ativar em outro computador"""
    license_key_id = request.data.get("licenseKeyId")
    fingerprint = request.data.get("fingerprint")

    def now_z():
        return timezone.now().isoformat().replace("+00:00", "Z")

    if not license_key_id or not fingerprint:
        return Response(
            {"detail": "licenseKeyId e fingerprint são obrigatórios", "serverUtc": now_z()},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not str(license_key_id).startswith("LIC_"):
        return Response(
            {"detail": "ID de licença inválido", "serverUtc": now_z()},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        license_id = int(str(license_key_id).replace("LIC_", ""))
        lic = License.objects.get(id=license_id)
    except (ValueError, License.DoesNotExist):
        return Response(
            {"detail": "Licença não encontrada", "serverUtc": now_z()},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verifica se a ativação existe
    activation = Activation.objects.filter(license=lic, fingerprint=fingerprint).first()

    if not activation:
        return Response(
            {"detail": "Licença não está ativada neste computador", "serverUtc": now_z()},
            status=status.HTTP_403_FORBIDDEN
        )

    # Remove a ativação
    activation.delete()

    return Response(
        {"detail": "Licença desativada com sucesso", "serverUtc": now_z()}
    )