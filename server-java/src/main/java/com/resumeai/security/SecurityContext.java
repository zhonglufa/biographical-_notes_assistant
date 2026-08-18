package com.resumeai.security;

/**
 * 当前请求的安全上下文持有者（ThreadLocal）。
 * 由 JwtAuthFilter 在过滤器链中 set，finally 中 clear，避免线程复用串号。
 */
public final class SecurityContext {

    private static final ThreadLocal<UserContext> HOLDER = new ThreadLocal<>();

    private SecurityContext() {
    }

    public static void set(UserContext ctx) {
        HOLDER.set(ctx);
    }

    public static void clear() {
        HOLDER.remove();
    }

    public static boolean isAuthenticated() {
        return HOLDER.get() != null;
    }

    /** 取当前用户上下文；未认证（理论上不应发生，过滤器已拦截）则 fail-closed 抛 CREDENTIAL_MISSING。 */
    public static UserContext current() {
        UserContext ctx = HOLDER.get();
        if (ctx == null) {
            throw AuthException.credentialMissing();
        }
        return ctx;
    }

    public static String currentUserId() {
        return current().userId();
    }

    public static String currentRole() {
        return current().role();
    }
}
