"""
Request / response schemas for the auth endpoints.
"""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    onboarded: bool
    favorite_genres: list[str] = Field(default_factory=list)
    watch_history_count: int = 0
    watchlist_count: int = 0
    ratings_count: int = 0
    liked_count: int = 0
