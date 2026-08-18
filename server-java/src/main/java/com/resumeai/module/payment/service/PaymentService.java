package com.resumeai.module.payment.service;

import com.resumeai.module.payment.dto.*;

public interface PaymentService {
    /** A20 创建会员订单（金额服务端权威计算）。 */
    OrderCreateResponse createOrder(String userId, OrderCreateRequest req);

    /** A21 支付渠道回调（验签 + 幂等 + 状态机；fail-closed 不发货）。 */
    void handleCallback(PaymentCallbackRequest req);
}
