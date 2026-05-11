from typing import Optional

from app.core.database import supabase
from app.core.security import get_password_hash, verify_password
from app.schemas.user import SignUpRequest, LoginRequest, SocialLoginRequest


def create_user(data: SignUpRequest) -> dict:
    """회원가입 (로컬 이메일 또는 소셜 provider_id)."""
    if data.login_type == "local":
        existing = supabase.table("users").select("id").eq("email", data.email).execute()
        if existing.data:
            raise ValueError("이미 사용 중인 이메일입니다.")

        insert_data = {
            "email": data.email,
            "password_hash": get_password_hash(data.password),
            "nickname": data.nickname,
            "login_type": "local",
            "total_points": 0,
        }
        if data.profile_image_url:
            insert_data["profile_image_url"] = data.profile_image_url

        result = supabase.table("users").insert(insert_data).execute()
        return result.data[0]

    existing = (
        supabase.table("users")
        .select("id")
        .eq("login_type", data.login_type)
        .eq("provider_id", data.provider_id)
        .execute()
    )
    if existing.data:
        raise ValueError("이미 연동된 소셜 계정입니다.")

    insert_data = {
        "email": data.email,
        "password_hash": None,
        "nickname": data.nickname,
        "login_type": data.login_type,
        "provider_id": data.provider_id,
        "total_points": 0,
    }
    if data.profile_image_url:
        insert_data["profile_image_url"] = data.profile_image_url

    result = supabase.table("users").insert(insert_data).execute()
    return result.data[0]


def authenticate_user(data: LoginRequest) -> Optional[dict]:
    """이메일 + 비밀번호 (로컬)."""
    result = supabase.table("users").select("*").eq("email", data.email).execute()
    if not result.data:
        return None

    user = result.data[0]
    if user.get("login_type") != "local":
        return None
    ph = user.get("password_hash")
    if not ph:
        return None
    if not verify_password(data.password, ph):
        return None
    return user


def authenticate_social(data: SocialLoginRequest) -> Optional[dict]:
    """소셜 로그인: 기존 행 조회만 (가입은 /signup)."""
    result = (
        supabase.table("users")
        .select("*")
        .eq("login_type", data.login_type)
        .eq("provider_id", data.provider_id)
        .execute()
    )
    if not result.data:
        return None
    return result.data[0]
