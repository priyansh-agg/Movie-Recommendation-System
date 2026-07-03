"""
JWT token creation and verification.

Uses HS256 symmetric signing.  The secret key MUST be changed
from the default in production (set JWT_SECRET_KEY in .env).
"""

import os
import time

from jose import jwt, JWTError


SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", "dev-secret-key-change-in-production"
)
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)


def create_access_token(user_id: int) -> str:
    """Create a short-lived access token."""
    payload = {
        "sub": str(user_id),
        "exp": time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived refresh token."""
    payload = {
        "sub": str(user_id),
        "exp": time.time() + REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> int | None:
    """Verify an access token.  Returns user_id or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if user_id and payload.get("type") == "access":
            return user_id
    except (JWTError, ValueError, KeyError):
        pass
    return None


def verify_refresh_token(token: str) -> int | None:
    """Verify a refresh token.  Returns user_id or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if user_id and payload.get("type") == "refresh":
            return user_id
    except (JWTError, ValueError, KeyError):
        pass
    return None
