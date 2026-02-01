"""
Encryption utilities for secure token storage using Fernet symmetric encryption.
"""
import os
from cryptography.fernet import Fernet
import base64
import hashlib

def get_encryption_key() -> bytes:
    """Get or generate encryption key from environment."""
    key = os.environ.get('ENCRYPTION_KEY')
    if key:
        return key.encode()
    
    # Derive a key from JWT_SECRET if ENCRYPTION_KEY not set
    jwt_secret = os.environ.get('JWT_SECRET', 'default-secret-key')
    # Create a valid Fernet key from JWT_SECRET
    key_bytes = hashlib.sha256(jwt_secret.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)

def get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    return Fernet(get_encryption_key())

def encrypt_token(token: str) -> str:
    """Encrypt a token for secure storage."""
    if not token:
        return ""
    fernet = get_fernet()
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a stored token."""
    if not encrypted_token:
        return ""
    fernet = get_fernet()
    return fernet.decrypt(encrypted_token.encode()).decode()
