-- 岗位浏览模块写表（Java 业务侧拥有；job 读表由 Python 采集器经 Alembic 迁移创建，本迁移不重复建）。
-- 注意：user_id 用 VARCHAR(36) 以对齐 Java 实体（沿用 P0 userId=String 约定）；时间戳用 BIGINT(epoch ms)。

CREATE TABLE IF NOT EXISTS job_match (
 user_id VARCHAR(36) NOT NULL,
 job_id BIGINT NOT NULL,
 resume_version_id BIGINT,
 score TINYINT NOT NULL,
 band ENUM('green','blue','gray') NOT NULL,
 reason VARCHAR(512),
 computed_at BIGINT NOT NULL,
 PRIMARY KEY (user_id, job_id),
 KEY (user_id, score)
) ;

CREATE TABLE IF NOT EXISTS job_favorite (
 user_id VARCHAR(36) NOT NULL,
 job_id BIGINT NOT NULL,
 action ENUM('favorite','ignore','removed') NOT NULL DEFAULT 'favorite',
 created_at BIGINT NOT NULL,
 PRIMARY KEY (user_id, job_id),
 KEY (job_id)
) ;

CREATE TABLE IF NOT EXISTS job_view (
 user_id VARCHAR(36) NOT NULL,
 id BIGINT NOT NULL AUTO_INCREMENT,
 job_id BIGINT NOT NULL,
 viewed_at BIGINT NOT NULL,
 source VARCHAR(32),
 PRIMARY KEY (id),
 KEY (job_id),
 KEY (user_id, viewed_at)
) ;
