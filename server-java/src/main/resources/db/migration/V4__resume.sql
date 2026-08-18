-- 简历工作台模块表（Java 业务侧；resume/resume_version/ats_report）
-- user_id VARCHAR(36) 对齐 P0 userId=String 约定；时间戳 BIGINT(epoch ms)；snapshot/suggestions 存 JSON。

CREATE TABLE IF NOT EXISTS resume (
  id                    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id              VARCHAR(36)     NOT NULL,
  title                VARCHAR(255)    NOT NULL,
  preferred_version_id BIGINT UNSIGNED,
  created_at           BIGINT          NOT NULL,
  updated_at           BIGINT          NOT NULL,
  PRIMARY KEY (id),
  KEY idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='简历头部(§6.13.5.2 一份简历多版本)';

CREATE TABLE IF NOT EXISTS resume_version (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  resume_id    BIGINT UNSIGNED NOT NULL,
  user_id      VARCHAR(36)     NOT NULL,
  version_no   INT UNSIGNED    NOT NULL,
  snapshot     JSON            NOT NULL COMMENT '解析后结构化简历(JSON，AES-256-GCM)',
  raw_file_ref VARCHAR(512)    COMMENT 'OSS 外链，原文不落库(ADR-003)',
  is_encrypted BOOLEAN         NOT NULL DEFAULT TRUE,
  created_at   BIGINT          NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_resume_ver (resume_id, version_no),
  KEY idx_resume (resume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='简历版本快照(快照式版本管理 ADR-012；投递锁定当时版本)';

CREATE TABLE IF NOT EXISTS ats_report (
  resume_version_id BIGINT UNSIGNED NOT NULL,
  ats_score         TINYINT UNSIGNED NOT NULL COMMENT '0-100',
  suggestions       JSON            NOT NULL COMMENT '改进建议[{section,hint}]',
  model             VARCHAR(64)     NOT NULL COMMENT '评分模型/规则标识',
  created_at        BIGINT          NOT NULL,
  PRIMARY KEY (resume_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ATS 评分报告(A06 触发 B05 回填，投递前自查)';
