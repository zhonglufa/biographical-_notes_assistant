package com.resumeai.common;

import jakarta.servlet.http.HttpServletRequest;
import java.util.UUID;

/**
 * 机器可读错误信封（对齐 design/contracts/error-envelope.schema.json）。
 * 字段：code(字符串业务码) / message / traceId / retryable(布尔) / user_action(可选)。
 * 与 ApiResponse(int code) 并存：AuthException 走本信封以确保契约一致；
 * BizException 沿用 ApiResponse 为既有偏差（待统一，见 PROJECT_BRAIN）。
 */
public record ErrorEnvelope(String code, String message, String traceId, boolean retryable, String userAction) {

    public static ErrorEnvelope of(String code, String message, HttpServletRequest req,
                                   boolean retryable, String userAction) {
        String trace = req.getHeader("X-Trace-Id");
        if (trace == null || trace.isBlank()) {
            trace = UUID.randomUUID().toString();
        }
        return new ErrorEnvelope(code, message, trace, retryable, userAction);
    }
}
