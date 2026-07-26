"""core/secrets.py — Secrets Rotation & Encryption at Rest (Sprint E5/F6)"""
from __future__ import annotations
import os
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet

def derive_key(master: str | None = None) -> bytes:
    master = master or os.getenv('MASTER_ENCRYPTION_KEY', 'dev-key-change-me-in-production')
    return base64.urlsafe_b64encode(hashlib.sha256(master.encode()).digest())

def encrypt_value(value: str, key: bytes | None = None) -> str:
    k = key or derive_key()
    f = Fernet(k)
    return f.encrypt(value.encode()).decode()

def decrypt_value(token: str, key: bytes | None = None) -> str:
    k = key or derive_key()
    f = Fernet(k)
    return f.decrypt(token.encode()).decode()

def hash_sensitive(data: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    return salt + ':' + hmac.new(salt.encode(), data.encode(), hashlib.sha256).hexdigest()

def verify_hash(data: str, salted_hash: str) -> bool:
    salt, h = salted_hash.split(':')
    return hmac.compare_digest(h, hmac.new(salt.encode(), data.encode(), hashlib.sha256).hexdigest())

MASTER_KEY = derive_key()
