import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_MAX_EXCERPT_CHARS = 500


def generate_job_key() -> bytes:
    """Generate a random 256-bit AES key for one job."""
    return os.urandom(32)


def encrypt_excerpt(plaintext: str, key: bytes) -> str:
    """Encrypt excerpt using AES-256-GCM. Returns base64-encoded nonce+ciphertext."""
    truncated = plaintext[:_MAX_EXCERPT_CHARS]
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, truncated.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_excerpt(token: str, key: bytes) -> str:
    """Decrypt an encrypted excerpt. Raises on wrong key or tampered data."""
    raw = base64.b64decode(token.encode())
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None).decode()
