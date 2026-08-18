package com.resumeai.security;

/**
 * 已认证用户上下文（由 JwtAuthFilter 在每次请求解析 JWT 后填充）。
 * 字段严格对应 HLD §3.1 / LLD 用户与权限 §90 的 JWT claims：sub / role / plan。
 */
public record UserContext(String userId, String role, String plan) {

    /** 匿名（未认证）角色；fail-closed 默认，不应出现在已通过过滤器的请求中。 */
    public static final String ANONYMOUS = "anonymous";

    public UserContext {
        if (userId == null || userId.isBlank()) {
            throw new IllegalArgumentException("userId 不可为空");
        }
        role = (role == null || role.isBlank()) ? "free" : role;
        plan = (plan == null || plan.isBlank()) ? role : plan;
    }
}
