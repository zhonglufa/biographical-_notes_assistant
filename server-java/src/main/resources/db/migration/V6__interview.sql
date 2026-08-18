-- P2 interview 模块 DDL（对齐 LLD-数据库设计 §3.4，MySQL 8.0 方言）
-- 注：H2 测试用 JPA create-drop 建表，本文件仅在主环境（Flyway 启用）执行。

CREATE TABLE interview_question_set (
  user_id        BIGINT UNSIGNED NOT NULL,
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  application_id BIGINT UNSIGNED,
  state          ENUM('generating','ready') NOT NULL DEFAULT 'generating',
  questions      JSON,
  created_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, id),
  UNIQUE KEY uk_id (id),
  KEY idx_user (user_id),
  KEY idx_app (application_id)
) COMMENT='题集(§6.16 G7-1)';

CREATE TABLE interview_session (
  user_id         BIGINT UNSIGNED NOT NULL,
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  question_set_id BIGINT UNSIGNED NOT NULL,
  application_id  BIGINT UNSIGNED,
  state ENUM('created','active','in_progress','paused','completed','scored','archived','abandoned') NOT NULL DEFAULT 'created',
  mode  ENUM('text','voice') NOT NULL DEFAULT 'text',
  current_turn INT UNSIGNED NOT NULL DEFAULT 0,
  started_at DATETIME(3),
  ended_at   DATETIME(3),
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (user_id, id),
  UNIQUE KEY uk_id (id),
  KEY idx_user (user_id),
  KEY idx_qs (question_set_id)
) COMMENT='面试会话(§6.16 G7-1)';

CREATE TABLE interview_question (
  id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id      BIGINT UNSIGNED NOT NULL,
  question_set_id BIGINT UNSIGNED NOT NULL,
  turn            INT UNSIGNED NOT NULL,
  text            TEXT NOT NULL,
  type            ENUM('behavior','tech','case') NOT NULL,
  expected_points JSON,
  jd_keywords_coverage DECIMAL(4,3),
  created_at      DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_session (session_id),
  KEY idx_set (question_set_id)
) COMMENT='单道面试题';

CREATE TABLE interview_answer (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id   BIGINT UNSIGNED NOT NULL,
  question_id  BIGINT UNSIGNED NOT NULL,
  turn         INT UNSIGNED NOT NULL,
  modality     ENUM('text','voice_asr') NOT NULL,
  asr_provider VARCHAR(32),
  answer_text  MEDIUMTEXT,
  turn_score   DECIMAL(4,3),
  rubric       JSON,
  created_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (id),
  KEY idx_session_turn (session_id, turn),
  KEY idx_session (session_id)
) COMMENT='逐轮作答';

CREATE TABLE interview_evaluation (
  session_id     BIGINT UNSIGNED NOT NULL,
  weighted_score TINYINT UNSIGNED NOT NULL,
  dimensions     JSON NOT NULL,
  degrade_flag   TINYINT(1) NOT NULL DEFAULT 0,
  appeal_entry   TINYINT(1) DEFAULT 0,
  rerun_entry    TINYINT(1) DEFAULT 0,
  created_at     DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY (session_id),
  KEY idx_score (weighted_score)
) COMMENT='评估报告(G7-2)';

CREATE TABLE interview_session_event (
  user_id   BIGINT UNSIGNED NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  session_id BIGINT UNSIGNED NOT NULL,
  from_state VARCHAR(32),
  to_state   VARCHAR(32),
  reason     VARCHAR(255),
  actor      VARCHAR(32) DEFAULT 'system',
  PRIMARY KEY (user_id, created_at, id),
  UNIQUE KEY uk_id (id),
  KEY idx_session (session_id)
) COMMENT='面试会话审计事件(G7-1)';
