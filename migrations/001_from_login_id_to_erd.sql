-- 기존 프로젝트(login_id 기반)에서 ERD 스키마로 옮길 때 참고용 스크립트입니다.
-- 데이터 보존이 필요하면 백업 후 단계별로 검토해 실행하세요.

-- 1) users: 신규 컬럼 추가
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS login_type VARCHAR(50) NOT NULL DEFAULT 'local';
ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_id VARCHAR(255);

-- 2) login_id → email (로컬 계정용 임시 도메인)
UPDATE users SET email = login_id || '@local.legacy' WHERE email IS NULL AND login_id IS NOT NULL;

-- 3) 제약·인덱스 (login_id 제거 전에 email·CHECK 준비)
--    (이미 schema.sql로 만든 DB면 이 파일은 건너뛰면 됩니다.)

-- ALTER TABLE users DROP COLUMN IF EXISTS login_id;
-- 이후 schema.sql 의 CHECK / UNIQUE 인덱스에 맞게 제약 추가
