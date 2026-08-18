-- 简历工作台模块表（Java 业务侧；resume/resume_version/ats_report）
-- user_id VARCHAR(36) 对齐 P0 userId=String 约定；时间戳 BIGINT(epoch ms)；snapshot/suggestions 存 TEXT。

CREATE TABLE IF NOT EXISTS resume (
 id BIGINT NOT NULL AUTO_INCREMENT,
 user_id VARCHAR(36) NOT NULL,
 title VARCHAR(255) NOT NULL,
 preferred_version_id BIGINT,
 created_at BIGINT NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 KEY (user_id)
) ;

CREATE TABLE IF NOT EXISTS resume_version (
 id BIGINT NOT NULL AUTO_INCREMENT,
 resume_id BIGINT NOT NULL,
 user_id VARCHAR(36) NOT NULL,
 version_no INT NOT NULL,
 snapshot TEXT NOT NULL COMMENT '解析后结构化简历(TEXT，AES-256-GCM)',
 raw_file_ref VARCHAR(512) COMMENT 'OSS 外链，原文不落库(ADR-003)',
 is_encrypted BOOLEAN NOT NULL DEFAULT TRUE,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 UNIQUE KEY (resume_id, version_no),
 KEY (resume_id)
) ;

CREATE TABLE IF NOT EXISTS ats_report (
 resume_version_id BIGINT NOT NULL,
 ats_score TINYINT NOT NULL COMMENT '0-100',
 suggestions TEXT NOT NULL COMMENT '改进建议[{section,hint}]',
 model VARCHAR(64) NOT NULL COMMENT '评分模型/规则标识',
 created_at BIGINT NOT NULL,
 PRIMARY KEY (resume_version_id)
) ;
