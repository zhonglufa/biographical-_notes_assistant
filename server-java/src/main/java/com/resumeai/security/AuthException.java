package com.resumeai.security;

import com.resumeai.common.ErrorEnvelope;

/**
 * 鉴权异常：携带机器可读错误码（对齐 design/contracts/error-codes.json）与 HTTP 状态。
 * 由 GlobalExceptionHandler（MVC 内，如 PermissionInterceptor 抛出）或 JwtAuthFilter
 * （过滤器阶段抛出，自行写入 ErrorEnvelope）统一转译为 {@link ErrorEnvelope}。
 *
 * <p>错误码语义：UNAUTHORIZED=令牌无效/缺失、CREDENTIAL_MISSING=缺凭证、
 * TOKEN_EXPIRED=过期、FORBIDDEN=权限不足。</p>
 */
public class AuthException extends RuntimeException {

    public final String code;
    public final int httpStatus;
    public final boolean retryable;
    public final String userAction;

    private AuthException(String code, int httpStatus, boolean retryable, String userAction, String message) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus;
        this.retryable = retryable;
        this.userAction = userAction;
    }

    public static AuthException unauthorized() {
        return new AuthException("UNAUTHORIZED", 401, false, "重新登录", "令牌无效或缺失");
    }

    public static AuthException credentialMissing() {
        return new AuthException("CREDENTIAL_MISSING", 401, false, "重新登录", "缺少访问凭证");
    }

    public static AuthException tokenExpired() {
        return new AuthException("TOKEN_EXPIRED", 401, false, "调用 refresh", "访问令牌已过期");
    }

    public static AuthException forbidden() {
        return new AuthException("FORBIDDEN", 403, false, "升级套餐或联系管理员", "无权限执行该操作");
    }
}
