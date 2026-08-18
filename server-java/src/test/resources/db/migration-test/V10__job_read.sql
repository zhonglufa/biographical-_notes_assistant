-- 测试专用：job 读表（生产环境由 Python 采集器经 Alembic 迁移创建，Java 侧 Flyway 不建）。
-- 为使 JobsServiceTest 在 H2（无 Python 采集器）下可跑，这里补建一份与 Job 实体对齐的 schema。
-- 仅存在于 migration-test，不进入生产 classpath:db/migration。

CREATE TABLE job (
  id           BIGINT NOT NULL AUTO_INCREMENT,
  platform_id  VARCHAR(36),
  external_id  VARCHAR(255),
  title        VARCHAR(255),
  company      VARCHAR(255),
  url          VARCHAR(512),
  salary_min   INT,
  salary_max   INT,
  location     VARCHAR(255),
  description  TEXT,
  jd_raw       TEXT,
  source       VARCHAR(32),
  collected_at BIGINT,
  PRIMARY KEY (id)
) ;
