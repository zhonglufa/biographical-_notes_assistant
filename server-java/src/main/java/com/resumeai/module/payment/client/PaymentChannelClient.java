package com.resumeai.module.payment.client;

import com.resumeai.module.payment.dto.PaymentCallbackRequest;

/**
 * 支付渠道门面（A21 回调验签）。
 * 真实实现应接微信/支付宝平台公钥验签（HLD §4.10）；当前为内存 stub。
 */
public interface PaymentChannelClient {
    /** 验签：失败表示伪造/篡改，调用方应拒收（fail-closed，不发货）。 */
    boolean verifySign(PaymentCallbackRequest req);
}
