-- ============================================================
-- 터줏대감 (TeoJutDeKam) 데이터베이스 스키마 (ERD 기준)
-- Supabase SQL Editor에서 실행하세요
-- ============================================================

-- USERS (이메일·소셜 식별자·로그인 유형)
CREATE TABLE IF NOT EXISTS users (
    id                  BIGSERIAL PRIMARY KEY,
    email               VARCHAR(255),
    password_hash       VARCHAR(255),
    nickname            VARCHAR(100) NOT NULL,
    profile_image_url   VARCHAR(500),
    login_type          VARCHAR(50) NOT NULL DEFAULT 'local',
    provider_id         VARCHAR(255),
    total_points        INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT users_auth_shape CHECK (
        (login_type = 'local' AND email IS NOT NULL AND password_hash IS NOT NULL)
        OR (login_type <> 'local' AND provider_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique
    ON users (email) WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_social_unique
    ON users (login_type, provider_id) WHERE provider_id IS NOT NULL;

-- STORES
CREATE TABLE IF NOT EXISTS stores (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    category    VARCHAR(100),
    address     VARCHAR(500),
    latitude    DECIMAL(10, 7) NOT NULL,
    longitude   DECIMAL(10, 7) NOT NULL,
    phone       VARCHAR(50),
    image_url   VARCHAR(500),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- VISIT_CERTIFICATIONS
CREATE TABLE IF NOT EXISTS visit_certifications (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id            BIGINT NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    user_latitude       DECIMAL(10, 7) NOT NULL,
    user_longitude      DECIMAL(10, 7) NOT NULL,
    distance_meters     INTEGER,
    certification_type  VARCHAR(50) NOT NULL,
    status              VARCHAR(50) NOT NULL DEFAULT 'pending',
    earned_points       INTEGER DEFAULT 0,
    certified_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- STORE_USER_STATS
CREATE TABLE IF NOT EXISTS store_user_stats (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id        BIGINT NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    total_points    INTEGER NOT NULL DEFAULT 0,
    visit_count     INTEGER NOT NULL DEFAULT 0,
    review_count    INTEGER NOT NULL DEFAULT 0,
    last_visited_at TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, store_id)
);

-- REVIEWS (방문 인증 1:1 — visit_certification_id 필수·유일)
CREATE TABLE IF NOT EXISTS reviews (
    id                      BIGSERIAL PRIMARY KEY,
    user_id                 BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id                BIGINT NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    visit_certification_id  BIGINT NOT NULL REFERENCES visit_certifications(id) ON DELETE CASCADE,
    rating                  INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    content                 TEXT,
    earned_points           INTEGER DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (visit_certification_id)
);

-- POINT_HISTORIES
CREATE TABLE IF NOT EXISTS point_histories (
    id                      BIGSERIAL PRIMARY KEY,
    user_id                 BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    store_id                BIGINT REFERENCES stores(id) ON DELETE SET NULL,
    visit_certification_id  BIGINT REFERENCES visit_certifications(id) ON DELETE SET NULL,
    review_id               BIGINT REFERENCES reviews(id) ON DELETE SET NULL,
    point_type              VARCHAR(50) NOT NULL,
    point_amount            INTEGER NOT NULL,
    description             TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visit_cert_user_id  ON visit_certifications (user_id);
CREATE INDEX IF NOT EXISTS idx_visit_cert_store_id ON visit_certifications (store_id);
CREATE INDEX IF NOT EXISTS idx_store_user_stats_store ON store_user_stats (store_id, total_points DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_store_id    ON reviews (store_id);
CREATE INDEX IF NOT EXISTS idx_point_histories_user ON point_histories (user_id);
