-- F1 闭合（HIGH·真实缺陷）：job 读表从未被创建。
-- 根因：原 V3__jobs.sql 注释称「job 读表由 Python 采集器经 Alembic 创建」，但 server-python 无任何建表代码，
--       致 GET /api/v1/jobs 在 resume_ai.job 缺失时必 500。
-- 决策（R1 自主拍板）：server-python 从未交付 Alembic 建表路径；本仓库 25 张业务表均由 server-java Flyway 拥有，
--       故由 server-java 显式建 job 表，与 job_match/job_view/job_favorite 同库、类型对齐（BIGINT UNSIGNED）。
--       不改动已跑过的 V3（避免 Flyway 校验和冲突），仅新增本迁移。
-- 对齐 module.jobs.entity.Job：id 自增主键；platform_id/external_id 业务键；salary 区间；source∈{search,detail}。

CREATE TABLE IF NOT EXISTS job (
  id           BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  platform_id  VARCHAR(128),
  external_id  VARCHAR(256),
  title        VARCHAR(256),
  company      VARCHAR(256),
  url          VARCHAR(1024),
  salary_min   INT,
  salary_max   INT,
  location     VARCHAR(128),
  description  TEXT,
  jd_raw       MEDIUMTEXT,
  source       VARCHAR(32),
  collected_at BIGINT,
  PRIMARY KEY (id),
  KEY idx_platform (platform_id),
  KEY idx_external (external_id),
  KEY idx_title (title),
  KEY idx_collected (collected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='岗位读模型(A07/A08 浏览；由采集器入库，Java 侧只读)';
