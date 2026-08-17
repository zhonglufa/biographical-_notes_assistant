package com.resumeai.module.user.dto;

import java.util.List;

/**
 * A01 登录响应：JWT + 套餐 + 权益。
 * 字段名对齐 design/contracts/auth-login.response.schema.json。
 */
public record LoginResponse(String token, String refreshToken, String plan, List<String> permissions) {
}
