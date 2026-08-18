-- 岗位浏览模块写表（Java 业务侧拥有；job 读表由 Python 采集器经 Alembic 迁移创建，本迁移不重复建）。
-- 注意：user_id 用 VARCHAR(36) 以对齐 Java 实体（沿用 P0 userId=String 约定）；时间戳用 BIGINT(epoch ms)。

CREATE TABLE IF NOT EXISTS job_match (
  user_id            VARCHAR(36)      NOT NULL,
  job_id             BIGINT UNSIGNED  NOT NULL,
  resume_version_id  BIGINT UNSIGNED,
  score              TINYINT UNSIGNED NOT NULL,
  band               ENUM('green','blue','gray') NOT NULL,
  reason             VARCHAR(512),
  computed_at        BIGINT           NOT NULL,
  PRIMARY KEY (user_id, job_id),
  KEY idx_score (user_id, score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户×岗位匹配度反范式缓存(A07 列表 O(1)/行读取)';

CREATE TABLE IF NOT EXISTS job_favorite (
  user_id    VARCHAR(36)      NOT NULL,
  job_id     BIGINT UNSIGNED  NOT NULL,
  action     ENUM('favorite','ignore','removed') NOT NULL DEFAULT 'favorite',
  created_at BIGINT           NOT NULL,
  PRIMARY KEY (user_id, job_id),
  KEY idx_job (job_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='岗位收藏/忽略/软删(A08；ignore 供状态机模块推荐过滤)';

CREATE TABLE IF NOT EXISTS job_view (
  user_id    VARCHAR(36)      NOT NULL,
  id         BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  job_id     BIGINT UNSIGNED  NOT NULL,
  viewed_at  BIGINT           NOT NULL,
  source     VARCHAR(32),
  PRIMARY KEY (id),
  KEY idx_job (job_id),
  KEY idx_user_time (user_id, viewed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='岗位浏览记录(§3.3 离线缓存辅助/最近浏览)';
