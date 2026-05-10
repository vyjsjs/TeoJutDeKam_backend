from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ─── Auth ────────────────────────────────────────────
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    profile_image_url: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class KakaoCallbackRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── User ────────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    email: str
    nickname: str
    profile_image_url: Optional[str] = None
    login_type: str
    total_points: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    profile_image_url: Optional[str] = None
