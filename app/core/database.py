from supabase import create_client, Client
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# SQLAlchemy Base — 런타임 API는 Supabase 클라이언트만 사용합니다.
# `app/models/*`, Alembic(autogenerate) 참조용으로 유지합니다.
Base = declarative_base()


def get_supabase() -> Client:
    """Supabase 클라이언트 인스턴스 반환 (싱글톤)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# 글로벌 인스턴스
supabase: Client = get_supabase()
