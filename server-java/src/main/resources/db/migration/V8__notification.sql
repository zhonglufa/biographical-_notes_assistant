-- P2 notification 模块 DDL（对齐 LLD-通知推送模块 §7 + DB 设计 notification 表，MySQL 8.0 方言）
-- user_id 用 VARCHAR(36) 与 Java String(36) 一致（已登记偏差）；notification_key 去重键（LLD §8）。
-- 注意：H2 测试用 JPA create-drop 建表，本文件仅主环境（Flyway 启用）执行。

CREATE TABLE notification (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id VARCHAR(36) NOT NULL,
  channel ENUM('push','inbox','email','sms') NOT NULL,
  level ENUM('L0','L1','L2','L3') NOT NULL DEFAULT 'L2',
  title VARCHAR(255) NOT NULL,
  body TEXT,
  read_flag TINYINT(1) NOT NULL DEFAULT 0,
  sent_at BIGINT UNSIGNED,
  created_at BIGINT UNSIGNED NOT NULL,
  notification_key VARCHAR(128) UNIQUE,
  PRIMARY KEY (id),
  KEY idx_user_read (user_id, read_flag),
  KEY idx_user_created (user_id, created_at)
) COMMENT='通知(站内信, 待通知模块 LLD 收口)';
