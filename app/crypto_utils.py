"""Encrypt/decrypt user API keys at rest."""

from __future__ import annotations

import os

from cryptography.fernet import Fernet, InvalidToken


def _fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is not set.")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_api_key(plain_key: str) -> str:
    return _fernet().encrypt(plain_key.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    try:
        return _fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt API key.") from exc


def generate_encryption_key() -> str:
    """Run once: python -c \"from app.crypto_utils import generate_encryption_key; print(generate_encryption_key())\" """
    return Fernet.generate_key().decode()
