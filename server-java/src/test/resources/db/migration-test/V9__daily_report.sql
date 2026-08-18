-- P3 daily-report 模块 DDL（对齐 LLD-每日日报模块 §0–§5 + DB 设计 daily_report / user_preference 表）
-- 约定（与团队已登记偏差一致）：
-- * user_id 用 VARCHAR(36) 与 Java String(36) 一致（DB LLD 写 BIGINT，偏差已登记）。
-- * 时间戳用 BIGINT epoch 毫秒（与 notification 等模块一致，非 DATETIME）。
-- * platform_breakdown 用 TEXT 存 TEXT 串（避免 H2/MySQL 间 TEXT 列类型差异）。
-- 注：测试环境用 JPA create-drop 从实体建表；本文件仅主环境（Flyway 启用）执行。

CREATE TABLE daily_report (
 user_id VARCHAR(36) NOT NULL,
 report_date VARCHAR(10) NOT NULL,
 total_applications INT NOT NULL DEFAULT 0,
 successful INT NOT NULL DEFAULT 0,
 failed INT NOT NULL DEFAULT 0,
 hr_views INT NOT NULL DEFAULT 0,
 interview_invitations INT NOT NULL DEFAULT 0,
 new_questions INT NOT NULL DEFAULT 0,
 platform_breakdown TEXT,
 sent_at BIGINT,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (user_id, report_date),
 KEY (user_id)
) COMMENT='日报快照, 每日每用户一条(§3.12)';

CREATE TABLE user_preference (
 user_id VARCHAR(36) NOT NULL,
 daily_report_push_time VARCHAR(5) NOT NULL DEFAULT '20:00' COMMENT 'HH:mm 推送时间(A25)',
 daily_report_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否推送日报(A25)',
 created_at BIGINT NOT NULL,
 updated_at BIGINT NOT NULL,
 PRIMARY KEY (user_id)
) COMMENT='用户偏好(§3.12 A25 日报推送时间；与 strategy_config 分离：投递策略 vs 通知偏好)';
