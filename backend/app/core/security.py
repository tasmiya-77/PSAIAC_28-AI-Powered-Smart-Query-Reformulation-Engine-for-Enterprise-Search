import time
import hmac
import hashlib
import base64
import json
from typing import Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

TOKEN_EXPIRE_SECONDS = 86400  # 24 hours


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(data_str: str) -> bytes:
    padding = "=" * ((4 - len(data_str) % 4) % 4)
    return base64.urlsafe_b64decode(data_str + padding)


def create_access_token(user_id: str, role: str = "Admin") -> str:
    """Generate a lightweight secure JWT session token."""
    secret = settings.JWT_SECRET.encode("utf-8")
    header = json.dumps({"alg": "HS256", "typ": "JWT"}).encode("utf-8")
    payload = json.dumps({
        "sub": user_id,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS
    }).encode("utf-8")

    encoded_header = _b64_encode(header)
    encoded_payload = _b64_encode(payload)
    message = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    
    signature = hmac.new(secret, message, hashlib.sha256).digest()
    encoded_signature = _b64_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def verify_token(token: str) -> bool:
    """Verify JWT session token format, signature, and expiration."""
    if not token or len(token.split(".")) != 3:
        return False

    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        secret = settings.JWT_SECRET.encode("utf-8")
        message = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_sig = _b64_encode(hmac.new(secret, message, hashlib.sha256).digest())

        if not hmac.compare_digest(encoded_signature, expected_sig):
            return False

        payload_bytes = _b64_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp", 0) < time.time():
            return False

        return True
    except Exception as e:
        logger.warning(f"Token verification error: {str(e)}")
        return False

