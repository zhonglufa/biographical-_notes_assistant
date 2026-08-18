-- P1 策略配置表（对齐 LLD-策略配置模块 §1 / LLD-数据库设计）
-- 每用户一行，uk(user_id) ≈ 主键；MySQL 8.0 方言。
CREATE TABLE strategy_config (
    user_id        VARCHAR(36) NOT NULL,
    match_threshold DOUBLE      NOT NULL DEFAULT 0.60,
    daily_limit    INT         NOT NULL DEFAULT 30,
    platforms_json TEXT,
    blacklist_json TEXT,
    updated_at     BIGINT      NOT NULL,
    PRIMARY KEY (user_id)
);
