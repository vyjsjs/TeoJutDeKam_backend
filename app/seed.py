"""
시드 데이터 스크립트
Supabase에 테스트 데이터 삽입
실행: python -m app.seed
"""
from app.core.database import supabase
from app.core.security import get_password_hash


SEED_STORES = [
    {
        "name": "경희대 정문 김밥천국",
        "category": "한식",
        "address": "서울특별시 동대문구 경희대로 26",
        "latitude": 37.5965,
        "longitude": 127.0512,
        "phone": "02-961-0001",
    },
    {
        "name": "회기역 이삭토스트",
        "category": "간식",
        "address": "서울특별시 동대문구 회기로 49",
        "latitude": 37.5896,
        "longitude": 127.0584,
        "phone": "02-961-0002",
    },
    {
        "name": "경희대 후문 순대국집",
        "category": "한식",
        "address": "서울특별시 동대문구 경희대로 30",
        "latitude": 37.5978,
        "longitude": 127.0498,
        "phone": "02-961-0003",
    },
    {
        "name": "외대앞 돈까스 전문점",
        "category": "일식",
        "address": "서울특별시 동대문구 이문로 107",
        "latitude": 37.5943,
        "longitude": 127.0581,
        "phone": "02-961-0004",
    },
    {
        "name": "회기 파스타 하우스",
        "category": "양식",
        "address": "서울특별시 동대문구 회기로 21",
        "latitude": 37.5901,
        "longitude": 127.0573,
        "phone": "02-961-0005",
    },
    {
        "name": "경희대 쪽문 떡볶이",
        "category": "분식",
        "address": "서울특별시 동대문구 경희대로 14",
        "latitude": 37.5952,
        "longitude": 127.0534,
        "phone": "02-961-0006",
    },
    {
        "name": "이문동 치킨집",
        "category": "치킨",
        "address": "서울특별시 동대문구 이문로 99",
        "latitude": 37.5937,
        "longitude": 127.0567,
        "phone": "02-961-0007",
    },
    {
        "name": "회기역 커피빈",
        "category": "카페",
        "address": "서울특별시 동대문구 회기로 50",
        "latitude": 37.5893,
        "longitude": 127.0579,
        "phone": "02-961-0008",
    },
    {
        "name": "경희대 피자스쿨",
        "category": "양식",
        "address": "서울특별시 동대문구 경희대로 20",
        "latitude": 37.5960,
        "longitude": 127.0522,
        "phone": "02-961-0009",
    },
    {
        "name": "동대문 삼겹살 맛집",
        "category": "한식",
        "address": "서울특별시 동대문구 이문로 115",
        "latitude": 37.5948,
        "longitude": 127.0595,
        "phone": "02-961-0010",
    },
]

SEED_USERS = [
    {"email": "test@example.com", "password": "test1234", "nickname": "테스트유저"},
    {"email": "demo@example.com", "password": "demo1234", "nickname": "데모유저"},
    {"email": "admin@example.com", "password": "admin1234", "nickname": "관리자"},
]


def seed():
    result = supabase.table("stores").select("id").limit(1).execute()
    if result.data:
        print("✅ 시드 데이터가 이미 존재합니다. 건너뜁니다.")
        return

    for user_data in SEED_USERS:
        supabase.table("users").insert(
            {
                "email": user_data["email"],
                "password_hash": get_password_hash(user_data["password"]),
                "nickname": user_data["nickname"],
                "login_type": "local",
                "total_points": 0,
            }
        ).execute()

    supabase.table("stores").insert(SEED_STORES).execute()

    print(f"✅ 시드 데이터 삽입 완료: {len(SEED_USERS)}명 유저, {len(SEED_STORES)}개 매장")
    print("🔑 테스트 계정: test@example.com / test1234")


if __name__ == "__main__":
    seed()
