from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.schemas.user import (
    SignUpRequest,
    LoginRequest,
    SocialLoginRequest,
    LoginResponse,
    UserResponse,
)
from app.services.auth_service import (
    create_user,
    authenticate_user,
    authenticate_social,
)

router = APIRouter(prefix="/api/auth", tags=["인증"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignUpRequest):
    """회원가입 (로컬: email+password / 소셜: login_type+provider_id)"""
    try:
        return create_user(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest):
    """로컬 로그인 (이메일 + 비밀번호) → user_id 반환"""
    user = authenticate_user(data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    return LoginResponse(
        user_id=user["id"],
        email=user.get("email"),
        nickname=user["nickname"],
        login_type=user.get("login_type") or "local",
    )


@router.post("/login/social", response_model=LoginResponse)
def login_social(data: SocialLoginRequest):
    """소셜 로그인 (이미 /signup 으로 등록된 계정만)"""
    user = authenticate_social(data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="등록되지 않은 소셜 계정입니다. 먼저 회원가입 해주세요.",
        )
    return LoginResponse(
        user_id=user["id"],
        email=user.get("email"),
        nickname=user["nickname"],
        login_type=user.get("login_type") or "local",
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """현재 사용자 정보 (X-User-ID 헤더)"""
    return current_user
