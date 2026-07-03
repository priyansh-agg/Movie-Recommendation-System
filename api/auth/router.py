"""
Authentication router — register, login, refresh.
"""

from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext

from api.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from api.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from api.dependencies import get_user_repo

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _safe_hash(password: str) -> str:
    """Hash password, truncating to 72 bytes (bcrypt limit)."""
    return pwd_context.hash(password[:72])


def _safe_verify(password: str, hashed: str) -> bool:
    """Verify password, truncating to 72 bytes (bcrypt limit)."""
    return pwd_context.verify(password[:72], hashed)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(req: RegisterRequest):
    """Register a new user and return JWT tokens."""
    repo = get_user_repo()

    if repo.exists_email(req.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    hashed = _safe_hash(req.password)
    user = repo.create(
        email=req.email,
        username=req.username,
        hashed_password=hashed,
    )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Authenticate and return JWT tokens."""
    repo = get_user_repo()
    user = repo.get_by_email(req.email)

    if user is None or not _safe_verify(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    """Exchange a refresh token for new access + refresh tokens."""
    user_id = verify_refresh_token(req.refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    repo = get_user_repo()
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user_id=user.id,
    )
