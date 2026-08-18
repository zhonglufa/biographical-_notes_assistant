package com.resumeai.module.payment.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/** A20 创建会员订单请求（对齐 payments-order.request；金额由服务端权威计算）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record OrderCreateRequest(String plan, int months, String couponCode) {
}
