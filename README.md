# 🏠 터줏대감 (TeoJutDeKam) Backend

위치 기반 매장 방문 인증 & 점령 순위 서비스 API

## 🚀 기술 스택

- **Framework**: FastAPI (Python 3.11+)
- **Database**: Supabase PostgreSQL + SQLAlchemy 2.0 (Async)
- **Auth**: 로컬 이메일·비밀번호 + 소셜(`login_type`·`provider_id`, ERD) (단순 `X-User-ID` 헤더)
- **Migrations**: Alembic
- **Container**: Docker + Docker Compose

## 📋 주요 기능

### 1. 인증 (Auth)
- 회원가입: 로컬(`email`+`password`) 또는 소셜(`login_type`+`provider_id`, `nickname`)
- 로그인: `POST /api/auth/login` (로컬), `POST /api/auth/login/social` (소셜)
- 로그인 시 `user_id` 반환 → 프론트에서 `X-User-ID` 헤더로 전송

### 2. 방문 인증 (Visit Certification)
- **GPS 인증**: 매장 50m 이내 진입 시 자동 인증 (Haversine 거리 계산)
- **영수증 인증**: 항상 승인 처리 (하는 척만)
- 인증 시 자동 포인트 지급

### 3. 포인트 & 순위
- 방문 인증: 10포인트
- 리뷰 작성: 5포인트
- 매장별 터줏대감 순위 (포인트 기반)
- 전체 유저 글로벌 랭킹

### 4. 매장
- 매장 목록/검색/필터
- 근처 매장 검색 (GPS 기반)
- 매장 상세 (방문 수, 리뷰 수, 평점)
- 터줏대감 리스트 표시

### 5. 리뷰
- 승인된 방문 인증당 리뷰 1건 (`visit_certification_id` 필수, ERD 1:1)
- 매장별 리뷰 목록
- 내 리뷰 목록

### 6. 마이페이지
- 내 정보/프로필 수정
- 포인트 내역
- 내가 터줏대감인 매장 목록
- 방문/리뷰 통계

## 🏗️ 프로젝트 구조

```
app/
├── core/
│   ├── config.py      # 환경 설정
│   ├── database.py    # DB 연결
│   └── security.py    # 비밀번호 해싱, X-User-ID 인증
├── models/
│   ├── user.py
│   ├── store.py
│   ├── visit_certification.py
│   ├── store_user_stats.py
│   ├── review.py
│   └── point_history.py
├── schemas/
│   ├── user.py
│   ├── store.py
│   ├── visit.py
│   ├── review.py
│   └── ranking.py
├── services/
│   ├── auth_service.py
│   ├── visit_service.py
│   ├── review_service.py
│   └── ranking_service.py
├── routers/
│   ├── auth.py
│   ├── stores.py
│   ├── visits.py
│   ├── reviews.py
│   ├── ranking.py
│   └── mypage.py
├── main.py
└── seed.py
```

## 🔧 실행 방법

### 사전 준비: Supabase 설정

1. [Supabase](https://supabase.com)에서 프로젝트 생성
2. Project Settings > Database > Connection string 에서 URI 복사
3. `.env` 파일에 DATABASE_URL 설정

### Docker Compose

```bash
docker compose up --build
```

### 로컬 실행

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# .env 파일 설정
cp .env.example .env
# .env 파일에서 Supabase DATABASE_URL 수정

# DB 시드 데이터
python -m app.seed

# 서버 실행
uvicorn app.main:app --reload
```

### API 문서

서버 실행 후: http://localhost:8000/docs (Swagger UI)

## 🔐 인증 방식 (MVP)

JWT를 사용하지 않고, 단순 `X-User-ID` 헤더 방식으로 인증합니다.

1. **회원가입**: `POST /api/auth/signup` → 유저 생성
2. **로그인**: `POST /api/auth/login` → `user_id` 반환
3. **인증 필요 API**: 요청 시 `X-User-ID: {user_id}` 헤더 추가

```bash
# 로그인 예시 (로컬)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test1234"}'

# 인증 필요 API 호출 예시
curl http://localhost:8000/api/auth/me \
  -H "X-User-ID: 1"
```

## 📧 테스트 계정 (시드 기준)

| 이메일 | 비밀번호 | 닉네임 |
|--------|----------|--------|
| test@example.com | test1234 | 테스트유저 |
| demo@example.com | demo1234 | 데모유저 |
| admin@example.com | admin1234 | 관리자 |

## 📡 API 엔드포인트 요약

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/api/auth/signup` | 회원가입 | ❌ |
| POST | `/api/auth/login` | 로컬 로그인 (email+password) | ❌ |
| POST | `/api/auth/login/social` | 소셜 로그인 (login_type+provider_id) | ❌ |
| GET | `/api/auth/me` | 내 정보 | ✅ |
| GET | `/api/stores` | 매장 목록 | ❌ |
| GET | `/api/stores/nearby` | 근처 매장 | ❌ |
| GET | `/api/stores/{id}` | 매장 상세 | ❌ |
| POST | `/api/stores` | 매장 등록 | ❌ |
| POST | `/api/visits/gps` | GPS 방문 인증 | ✅ |
| POST | `/api/visits/receipt` | 영수증 인증 | ✅ |
| GET | `/api/visits/my` | 내 방문 내역 | ✅ |
| POST | `/api/reviews` | 리뷰 작성 | ✅ |
| GET | `/api/reviews/store/{id}` | 매장 리뷰 | ❌ |
| GET | `/api/reviews/my` | 내 리뷰 | ✅ |
| GET | `/api/ranking/store/{id}` | 매장 터줏대감 순위 | ❌ |
| GET | `/api/ranking/global` | 전체 순위 | ❌ |
| GET | `/api/ranking/my/stores` | 내 터줏대감 매장 | ✅ |
| GET | `/api/ranking/my/points` | 내 포인트 내역 | ✅ |
| GET | `/api/mypage/profile` | 프로필 조회 | ✅ |
| PUT | `/api/mypage/profile` | 프로필 수정 | ✅ |
| GET | `/api/mypage/summary` | 마이페이지 요약 | ✅ |
