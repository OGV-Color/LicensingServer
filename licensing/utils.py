import secrets
import string

def generate_license_key():
    alphabet = string.ascii_uppercase + string.digits
    parts = []
    for _ in range(4):
        part = ''.join(secrets.choice(alphabet) for _ in range(4))
        parts.append(part)
    return '-'.join(parts)