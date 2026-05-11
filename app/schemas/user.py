from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import datetime


class SignUpRequest(BaseModel):
    """로컬: email + password 필수. 소셜: login_type + provider_id 필수, password 생략."""
    nickname: str
    profile_image_url: Optional[str] = None
    login_type: str = "local"
    email: Optional[str] = None
    password: Optional[str] = None
    provider_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_auth_fields(self):
        if self.login_type == "local":
            if not self.email or not self.password:
                raise ValueError("로컬 가입은 email과 password가 필요합니다.")
        else:
            if not self.provider_id:
                raise ValueError("소셜 가입은 provider_id가 필요합니다.")
        return self


class LoginRequest(BaseModel):
    email: str
    password: str


class SocialLoginRequest(BaseModel):
    login_type: str
    provider_id: str


class LoginResponse(BaseModel):
    user_id: int
    email: Optional[str] = None
    nickname: str
    login_type: str = "local"
    message: str = "로그인 성공"


class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    nickname: str
    profile_image_url: Optional[str] = None
    total_points: int
    login_type: str = "local"
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    profile_image_url: Optional[str] = None
