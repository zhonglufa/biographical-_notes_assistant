-- P2 interview 模块 DDL（对齐 LLD-数据库设计 §3.4，MySQL 8.0 方言）
-- 注：H2 测试用 JPA create-drop 建表，本文件仅在主环境（Flyway 启用）执行。

CREATE TABLE interview_question_set (
 user_id        VARCHAR(36) NOT NULL,
 id BIGINT NOT NULL AUTO_INCREMENT,
 application_id BIGINT,
 state ENUM('generating','ready') NOT NULL DEFAULT 'generating',
 questions TEXT,
 created_at BIGINT NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY (user_id, id),
 UNIQUE KEY (id),
 KEY (user_id),
 KEY (application_id)
) COMMENT='题集(§6.16 G7-1)';

CREATE TABLE interview_session (
 user_id        VARCHAR(36) NOT NULL,
 id BIGINT NOT NULL AUTO_INCREMENT,
 question_set_id BIGINT NOT NULL,
 application_id BIGINT,
 state ENUM('created','active','in_progress','paused','completed','scored','archived','abandoned') NOT NULL DEFAULT 'created',
 mode ENUM('text','voice') NOT NULL DEFAULT 'text',
 current_turn INT NOT NULL DEFAULT 0,
 started_at BIGINT,
 ended_at BIGINT,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (user_id, id),
 UNIQUE KEY (id),
 KEY (user_id),
 KEY (question_set_id)
) COMMENT='面试会话(§6.16 G7-1)';

CREATE TABLE interview_question (
 id BIGINT NOT NULL AUTO_INCREMENT,
 session_id BIGINT NOT NULL,
 question_set_id BIGINT NOT NULL,
 turn INT NOT NULL,
 text TEXT NOT NULL,
 type ENUM('behavior','tech','case') NOT NULL,
 expected_points TEXT,
 jd_keywords_coverage DECIMAL(4,3),
 created_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 KEY (session_id),
 KEY (question_set_id)
) COMMENT='单道面试题';

CREATE TABLE interview_answer (
 id BIGINT NOT NULL AUTO_INCREMENT,
 session_id BIGINT NOT NULL,
 question_id BIGINT NOT NULL,
 turn INT NOT NULL,
 modality ENUM('text','voice_asr') NOT NULL,
 asr_provider VARCHAR(32),
 answer_text MEDIUMTEXT,
 turn_score DECIMAL(4,3),
 rubric TEXT,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 KEY (session_id, turn),
 KEY (session_id)
) COMMENT='逐轮作答';

CREATE TABLE interview_evaluation (
 session_id BIGINT NOT NULL,
 weighted_score TINYINT NOT NULL,
 dimensions TEXT NOT NULL,
 degrade_flag TINYINT(1) NOT NULL DEFAULT 0,
 appeal_entry TINYINT(1) DEFAULT 0,
 rerun_entry TINYINT(1) DEFAULT 0,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (session_id),
 KEY (weighted_score)
) COMMENT='评估报告(G7-2)';

CREATE TABLE interview_session_event (
 user_id        VARCHAR(36) NOT NULL,
 created_at BIGINT NOT NULL,
 id BIGINT NOT NULL AUTO_INCREMENT,
 session_id BIGINT NOT NULL,
 from_state VARCHAR(32),
 to_state VARCHAR(32),
 reason VARCHAR(255),
 actor VARCHAR(32) DEFAULT 'system',
 PRIMARY KEY (user_id, created_at, id),
 UNIQUE KEY (id),
 KEY (session_id)
) COMMENT='面试会话审计事件(G7-1)';
