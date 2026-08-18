package com.resumeai.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * JWT 配置（RS256 无状态令牌，HLD §3.1 ADR-017/018）。
 * P0 仅结构；RS256 密钥注入与签发逻辑在「安全横切批次」补。
 */
@ConfigurationProperties(prefix = "resumeai.jwt")
public record JwtProperties(
        String issuer,
        String publicKey,
        long accessTtlSeconds,
        long refreshTtlSeconds) {
}
