from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import secrets
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import bcrypt
from app.core.config import settings

# Initialize Argon2 password hasher
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with Argon2id primary and bcrypt fallback."""
    if not hashed_password or not plain_password:
        return False

    # Check for Argon2 hash format ($argon2id$...)
    if hashed_password.startswith("$argon2"):
        try:
            return ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    # Check for bcrypt hash format ($2b$, $2a$, $2y$)
    if hashed_password.startswith("$2"):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    return False


def get_password_hash(password: str) -> str:
    """Generate secure Argon2id hash."""
    return ph.hash(password)


def create_access_token(
    subject: Union[str, Any],
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate JWT containing sub, role, iat, and exp claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token for email verification and password reset."""
    return secrets.token_urlsafe(length)
