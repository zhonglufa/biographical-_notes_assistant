-- 用户表（Java 业务侧拥有；LLD-用户与权限模块 v1.0）。
-- 字段与 com.resumeai.module.user.entity.User 对齐：
--   id BIGINT UNSIGNED AUTO_INCREMENT / email / phone / password_hash / plan。
-- plan ∈ {free, pro, premium, admin}（HLD §3.1 权益矩阵），默认 free。
--
-- 修复说明：此前 V1~V9 漏建此表。UserServiceImpl 当前为内存 mock、未触达 DB，
-- 故此前启动/测试均未暴露；但一旦按设计接入真实 UserRepository(@TableName t_user)，
-- 缺表即崩溃。此处补齐以闭合 schema（真实缺陷修复，非新功能）。
CREATE TABLE IF NOT EXISTS t_user (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email         VARCHAR(255),
  phone         VARCHAR(64),
  password_hash VARCHAR(255),
  plan          VARCHAR(32) NOT NULL DEFAULT 'free' COMMENT 'free/pro/premium/admin',
  PRIMARY KEY (id),
  UNIQUE KEY uk_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表(LLD-用户与权限)';
