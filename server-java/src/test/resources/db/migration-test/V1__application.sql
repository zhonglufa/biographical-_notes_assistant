-- ============================================================
-- V1 投递域表结构（MySQL 8.0 · 对齐 LLD-数据库设计 §2.1 / HLD §3.4）
-- 字符集 utf8mb4_0900_ai_ci；引擎 InnoDB。
-- 生产由 Flyway 在应用启动时执行；测试环境使用 H2 + ddl-auto=create-drop（见 src/test/resources/application.yml）。
-- ============================================================

CREATE TABLE IF NOT EXISTS application (
 id VARCHAR(36) NOT NULL,
 user_id VARCHAR(36) NOT NULL,
 job_id VARCHAR(64) NOT NULL,
 platform_id VARCHAR(64) NOT NULL,
 status VARCHAR(20) NOT NULL,
 resume_version_id VARCHAR(36) NULL,
 idempotency_key VARCHAR(64) NULL,
 apply_date VARCHAR(10) NOT NULL,
 created_at BIGINT NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 UNIQUE (user_id, platform_id, job_id, apply_date),
 INDEX (user_id)
) ;

CREATE TABLE IF NOT EXISTS application_event (
 id VARCHAR(36) NOT NULL,
 user_id VARCHAR(36) NOT NULL,
 application_id VARCHAR(36) NOT NULL,
 from_state VARCHAR(20) NULL,
 to_state VARCHAR(20) NULL,
 reason TEXT NULL,
 occurred_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 INDEX (application_id)
) ;

CREATE TABLE IF NOT EXISTS application_task (
 id VARCHAR(36) NOT NULL,
 user_id VARCHAR(36) NOT NULL,
 application_id VARCHAR(36) NOT NULL,
 idempotency_key VARCHAR(64) NULL,
 platform_id VARCHAR(64) NULL,
 job_id VARCHAR(64) NULL,
 status VARCHAR(20) NULL,
 outcome VARCHAR(20) NULL,
 platform_apply_id VARCHAR(64) NULL,
 fail_reason TEXT NULL,
 evidence TEXT NULL,
 created_at BIGINT NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 INDEX (application_id)
) ;
