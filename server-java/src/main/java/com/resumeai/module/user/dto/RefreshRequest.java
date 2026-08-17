package com.resumeai.module.user.dto;

/**
 * A02 刷新令牌请求。字段对齐 auth-refresh.request.schema.json。
 */
public record RefreshRequest(String refreshToken) {
}
