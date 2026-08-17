package com.resumeai.module.user.dto;

import java.util.List;

/**
 * A03 当前用户信息。字段对齐 user-me.response.schema.json。
 */
public record UserMeResponse(Long userId, String email, String phone, String plan, List<String> permissions) {
}
