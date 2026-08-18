-- P2 payment 模块 DDL（对齐 LLD-支付模块 §1/§10，MySQL 8.0 方言）
-- 状态枚举已补 activated/expired（payment LLD §10 建议），保留 closed 作未支付逾期终态。
-- 注意：H2 测试用 JPA create-drop 建表，本文件仅主环境（Flyway 启用）执行。

CREATE TABLE member_order (
 id BIGINT NOT NULL AUTO_INCREMENT,
 order_no VARCHAR(64) NOT NULL,
 user_id VARCHAR(36) NOT NULL,
 plan ENUM('pro','team') NOT NULL,
 months INT NOT NULL,
 amount INT NOT NULL COMMENT '整数分',
 status ENUM('pending','paid','activated','expired','refunded','closed') NOT NULL DEFAULT 'pending',
 coupon_code VARCHAR(64),
 expire_at BIGINT NOT NULL COMMENT 'epoch ms',
 paid_at BIGINT,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (id),
 UNIQUE KEY (order_no),
 KEY (user_id)
) COMMENT='会员订单(资金链路权威, R-04)';
