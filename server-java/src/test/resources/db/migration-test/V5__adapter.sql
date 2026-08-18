-- 适配器模块表（Java 业务侧编排；平台执行在本机 Agent，服务端不直连平台/不存 Cookie）
-- user_id VARCHAR(36) 对齐 P0 userId=String 约定；时间戳 BIGINT(epoch ms)。

CREATE TABLE IF NOT EXISTS adapter_registry (
 platform_id VARCHAR(32) NOT NULL,
 version VARCHAR(32) NOT NULL,
 status ENUM('active','deprecated','disabled') NOT NULL DEFAULT 'active',
 checksum VARCHAR(128),
 signature VARCHAR(256),
 created_at BIGINT NOT NULL,
 PRIMARY KEY (platform_id, version)
) ;

CREATE TABLE IF NOT EXISTS user_adapter (
 user_id VARCHAR(36) NOT NULL,
 platform_id VARCHAR(32) NOT NULL,
 enabled BOOLEAN NOT NULL DEFAULT TRUE,
 created_at BIGINT NOT NULL,
 PRIMARY KEY (user_id, platform_id)
) ;
