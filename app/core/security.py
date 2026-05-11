from typing import Optional

from passlib.context import CryptContext
from fastapi import HTTPException, Header, status

from app.core.database import supabase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> dict:
    """X-User-ID 헤더에서 사용자 ID를 읽어 인증 처리 (MVP 단순 인증)"""
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다. X-User-ID 헤더를 설정해주세요.",
        )

    try:
        user_id = int(x_user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 사용자 ID입니다.",
        )

    result = supabase.table("users").select("*").eq("id", user_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
        )

    return result.data[0]


def get_current_user_optional(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> Optional[dict]:
    """Returns user dict if X-User-ID header is present, None otherwise."""
    if x_user_id is None:
        return None

    try:
        user_id = int(x_user_id)
    except (ValueError, TypeError):
        return None

    result = supabase.table("users").select("*").eq("id", user_id).execute()
    return result.data[0] if result.data else None
