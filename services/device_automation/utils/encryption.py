import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    key_b64 = os.environ.get("ENCRYPTION_KEY", "")
    if not key_b64:
        raise ValueError("ENCRYPTION_KEY environment variable not set")
    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY must be 32 bytes (base64-encoded)")
    return key


def encrypt_value(plaintext: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ct).decode("utf-8")


def decrypt_value(ciphertext_b64: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    data = base64.b64decode(ciphertext_b64)
    nonce = data[:12]
    ct = data[12:]
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext.decode("utf-8")
