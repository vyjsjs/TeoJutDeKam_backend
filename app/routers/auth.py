from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.user import (
    SignUpRequest,
    LoginRequest,
    KakaoCallbackRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    create_user,
    authenticate_user,
    generate_token,
    kakao_login,
)

router = APIRouter(prefix="/api/auth", tags=["인증"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: SignUpRequest, db: AsyncSession = Depends(get_db)):
    """자체 회원가입"""
    try:
        user = await create_user(db, data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """자체 로그인 (이메일/비밀번호)"""
    user = await authenticate_user(db, data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    token = generate_token(user)
    return TokenResponse(access_token=token)


@router.get("/kakao")
async def kakao_auth_redirect():
    """카카오 OAuth 로그인 리다이렉트 URL 반환"""
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    return {"auth_url": kakao_auth_url}


@router.get("/kakao/callback")
async def kakao_callback(code: str, db: AsyncSession = Depends(get_db)):
    """카카오 OAuth 콜백 처리"""
    try:
        user, token = await kakao_login(db, code)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/kakao/token", response_model=TokenResponse)
async def kakao_token_login(data: KakaoCallbackRequest, db: AsyncSession = Depends(get_db)):
    """프론트에서 받은 카카오 인가 코드로 로그인 처리 (SPA용)"""
    try:
        user, token = await kakao_login(db, data.code)
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return current_user
