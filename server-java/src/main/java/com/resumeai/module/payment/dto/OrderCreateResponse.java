package com.resumeai.module.payment.dto;

/** A20 创建会员订单响应（对齐 payments-order.response；amount 为整数分）。 */
public record OrderCreateResponse(String orderNo, String payUrl, int amount, long expireAt) {
}
