package com.resumeai.common;

/**
 * 业务异常：携带可机读 code（对齐 error-codes.json），由 GlobalExceptionHandler 统一转 HTTP 响应。
 */
public class BizException extends RuntimeException {
    public final int code;

    public BizException(int code, String message) {
        super(message);
        this.code = code;
    }

    public int getCode() {
        return code;
    }
}
