package com.resumeai.module.payment.client;

import com.resumeai.module.payment.dto.PaymentCallbackRequest;
import org.springframework.stereotype.Component;

/**
 * TODO: 接微信 Wechatpay-Signature / 支付宝 sign + 平台公钥验签（HLD §4.10）。
 * 当前内存桩：默认验签通过，仅供编译与链路验证，不得用于生产。
 */
@Component
public class InMemoryPaymentChannelClient implements PaymentChannelClient {
    @Override
    public boolean verifySign(PaymentCallbackRequest req) {
        return true; // 内存桩：默认通过
    }
}
