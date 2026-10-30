import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from app.core.config import settings

# Argon2 password hasher
ph = PasswordHasher()


def get_password_hash(password: str) -> str:
    """Hash password securely using Argon2."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against Argon2 hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# Helper to get a deterministic 32-byte Fernet key from the secret key
def _get_fernet_key() -> bytes:
    key_hash = hashlib.sha256(settings.APP_SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_secret(secret_text: str) -> str:
    """Encrypt sensitive values like GitHub OAuth tokens."""
    f = Fernet(_get_fernet_key())
    return f.encrypt(secret_text.encode()).decode()


def decrypt_secret(encrypted_text: str) -> str:
    """Decrypt sensitive values."""
    f = Fernet(_get_fernet_key())
    return f.decrypt(encrypted_text.encode()).decode()

