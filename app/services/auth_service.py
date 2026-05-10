from datetime import timedelta
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.schemas.user import SignUpRequest, LoginRequest


async def create_user(db: AsyncSession, data: SignUpRequest) -> User:
    """Create a new local user."""
    # Check existing email
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("이미 등록된 이메일입니다.")

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        nickname=data.nickname,
        profile_image_url=data.profile_image_url,
        login_type="local",
        total_points=0,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, data: LoginRequest) -> Optional[User]:
    """Authenticate a local user by email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash:
        return None
    if not verify_password(data.password, user.password_hash):
        return None
    return user


def generate_token(user: User) -> str:
    """Generate JWT access token for user."""
    return create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


async def kakao_login(db: AsyncSession, code: str) -> tuple[User, str]:
    """
    Exchange Kakao auth code for access token, then get/create user.
    Returns (user, jwt_token).
    """
    # 1. Exchange code for Kakao access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "client_secret": settings.KAKAO_CLIENT_SECRET,
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_data = token_response.json()

        if "access_token" not in token_data:
            raise ValueError(f"카카오 토큰 발급 실패: {token_data.get('error_description', 'Unknown error')}")

        kakao_access_token = token_data["access_token"]

        # 2. Get user info from Kakao
        user_response = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {kakao_access_token}"},
        )
        user_data = user_response.json()

    kakao_id = str(user_data["id"])
    kakao_account = user_data.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    email = kakao_account.get("email", f"kakao_{kakao_id}@teojutdekam.app")
    nickname = profile.get("nickname", f"카카오유저{kakao_id[:6]}")
    profile_image = profile.get("profile_image_url")

    # 3. Find or create user
    result = await db.execute(
        select(User).where(User.provider_id == kakao_id, User.login_type == "kakao")
    )
    user = result.scalar_one_or_none()

    if not user:
        # Check if email already exists (from local signup)
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            # Link Kakao to existing account
            existing.provider_id = kakao_id
            existing.login_type = "kakao"
            if not existing.profile_image_url and profile_image:
                existing.profile_image_url = profile_image
            user = existing
        else:
            user = User(
                email=email,
                nickname=nickname,
                profile_image_url=profile_image,
                login_type="kakao",
                provider_id=kakao_id,
                total_points=0,
            )
            db.add(user)

    await db.flush()
    await db.refresh(user)

    token = generate_token(user)
    return user, token
