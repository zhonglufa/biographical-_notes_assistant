package com.resumeai.module.user.dto;

import java.util.List;

/**
 * A03 权益矩阵响应。字段对齐权限校验上下文（HLD §4.1）。
 */
public record PermissionsResponse(List<String> permissions) {
}
