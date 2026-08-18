package com.resumeai.common;

import com.resumeai.security.AuthException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常拦截：
 * - 鉴权异常(AuthException) → 401/403 + 机器可读 ErrorEnvelope（对齐 error-envelope.schema.json）；
 * - 业务异常(BizException) → 400 + ApiResponse（既有，待统一为 ErrorEnvelope）；
 * - 其余 → 500。
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(AuthException.class)
    public ResponseEntity<ErrorEnvelope> handleAuth(AuthException ex, HttpServletRequest req) {
        return ResponseEntity.status(ex.httpStatus)
                .body(ErrorEnvelope.of(ex.code, ex.getMessage(), req, ex.retryable, ex.userAction));
    }

    @ExceptionHandler(BizException.class)
    public ResponseEntity<ApiResponse<Void>> handleBiz(BizException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.fail(ex.code, ex.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleOther(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.fail(500, ex.getMessage()));
    }
}
