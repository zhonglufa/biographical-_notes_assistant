package com.resumeai.module.user.dto;

/**
 * A01 登录请求。type ∈ {email, phone, wechat}（HLD §3.1）。
 * 字段名对齐 design/contracts/auth-login.request.schema.json。
 */
public record LoginRequest(String account, String credential, String type) {
}
