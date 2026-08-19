-- 测试专用：t_user（与 User 实体对齐）。仅 migration-test，不进生产 classpath:db/migration。
-- 风格对齐 V1~V10(test)：无 ENGINE/COLLATE/AUTO_INCREMENT 之外的 MySQL 专属子句，H2 MODE=MySQL 兼容。
CREATE TABLE IF NOT EXISTS t_user (
  id            BIGINT NOT NULL AUTO_INCREMENT,
  email         VARCHAR(255),
  phone         VARCHAR(64),
  password_hash VARCHAR(255),
  plan          VARCHAR(32) NOT NULL DEFAULT 'free',
  PRIMARY KEY (id),
  UNIQUE (email)
) ;
