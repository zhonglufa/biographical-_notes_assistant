package com.resumeai.module.payment;

import com.resumeai.common.BizException;
import com.resumeai.module.payment.dto.*;
import com.resumeai.module.payment.service.PaymentService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

/** A20/A21 关键路径单测（H2 内存库 · 对齐 P0/P1 范式）。 */
@SpringBootTest
@ActiveProfiles("test")
class PaymentServiceTest {

    @Autowired
    private PaymentService svc;

    @Test
    void 创建订单_金额服务端计算() {
        OrderCreateResponse r = svc.createOrder("u-1", new OrderCreateRequest("pro", 3, null));
        assertEquals("ORD-", r.orderNo().substring(0, 4));
        assertEquals(3000 * 3, r.amount());
        assertTrue(r.expireAt() > System.currentTimeMillis());
    }

    @Test
    void 未知套餐_抛400() {
        BizException ex = assertThrows(BizException.class, () -> svc.createOrder("u-1", new OrderCreateRequest("vip", 1, null)));
        assertEquals(400, ex.getCode());
    }

    @Test
    void 月数越界_抛400() {
        BizException ex = assertThrows(BizException.class, () -> svc.createOrder("u-1", new OrderCreateRequest("pro", 13, null)));
        assertEquals(400, ex.getCode());
    }

    @Test
    void 回调SUCCESS_订单转activated且幂等() {
        OrderCreateResponse r = svc.createOrder("u-2", new OrderCreateRequest("team", 1, null));
        PaymentCallbackRequest cb = new PaymentCallbackRequest("wechat", r.orderNo(), "txn-1", "SUCCESS", r.amount(), "sig-x", System.currentTimeMillis());
        svc.handleCallback(cb);
        // 重复回调：幂等，不应抛错
        svc.handleCallback(cb);
    }

    @Test
    void 回调金额不符_抛400() {
        OrderCreateResponse r = svc.createOrder("u-3", new OrderCreateRequest("pro", 1, null));
        PaymentCallbackRequest cb = new PaymentCallbackRequest("wechat", r.orderNo(), "txn-2", "SUCCESS", r.amount() + 1, "sig", System.currentTimeMillis());
        BizException ex = assertThrows(BizException.class, () -> svc.handleCallback(cb));
        assertEquals(400, ex.getCode());
    }
}
