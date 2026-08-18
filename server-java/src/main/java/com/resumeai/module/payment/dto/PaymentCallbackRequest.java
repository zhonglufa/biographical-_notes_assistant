package com.resumeai.module.payment.dto;

/**
 * A21 支付渠道回调请求（对齐 payments-callback.request；渠道非对称签名验签，不经本机 Agent）。
 * 注意：本 DTO 仅承载契约字段；A21 响应 schema 在 HLD §4.10 登记为 pending，故无响应体约束。
 */
public record PaymentCallbackRequest(String channel, String outTradeNo, String transactionId,
                                     String tradeStatus, int amount, String sign, long timestamp) {
}
