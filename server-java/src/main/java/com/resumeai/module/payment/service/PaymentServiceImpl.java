package com.resumeai.module.payment.service;

import com.resumeai.common.BizException;
import com.resumeai.module.payment.client.PaymentChannelClient;
import com.resumeai.module.payment.dto.*;
import com.resumeai.module.payment.entity.MemberOrder;
import com.resumeai.module.payment.repository.MemberOrderRepository;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Random;

@Service
public class PaymentServiceImpl implements PaymentService {

    private final MemberOrderRepository orderRepo;
    private final PaymentChannelClient channel;
    private final Random rnd = new Random();

    // 服务端权威价目表（整数分/月）；TODO: 接配置中心真实定价（payment LLD T-PAY-3）
    private static final Map<String, Integer> PRICE_PER_MONTH = Map.of("pro", 3000, "team", 9000);

    public PaymentServiceImpl(MemberOrderRepository orderRepo, PaymentChannelClient channel) {
        this.orderRepo = orderRepo;
        this.channel = channel;
    }

    @Override
    public OrderCreateResponse createOrder(String userId, OrderCreateRequest req) {
        if (!PRICE_PER_MONTH.containsKey(req.plan())) {
            throw new BizException(400, "未知套餐: " + req.plan());
        }
        if (req.months() < 1 || req.months() > 12) {
            throw new BizException(400, "购买月数须在 1..12");
        }
        int amount = PRICE_PER_MONTH.get(req.plan()) * req.months(); // 服务端权威算价，客户端不可篡改
        long now = System.currentTimeMillis();
        MemberOrder o = new MemberOrder();
        o.setOrderNo("ORD-" + now + "-" + Math.abs(rnd.nextInt(100000)));
        o.setUserId(userId);
        o.setPlan(req.plan());
        o.setMonths(req.months());
        o.setAmount(amount);
        o.setCouponCode(req.couponCode());
        o.setStatus("pending");
        o.setExpireAt(now + 24L * 3600 * 1000); // 24h 过期
        o.setCreatedAt(now);
        orderRepo.save(o);
        return new OrderCreateResponse(o.getOrderNo(), "https://pay.example.com/cashier/" + o.getOrderNo(), amount, o.getExpireAt());
    }

    @Override
    public void handleCallback(PaymentCallbackRequest req) {
        if (!channel.verifySign(req)) {
            throw new BizException(400, "PAY_SIGN_INVALID"); // 验签失败：不发货、不回执成功
        }
        MemberOrder o = orderRepo.findByOrderNo(req.outTradeNo()).orElse(null);
        if (o == null) {
            // 订单不存在：已接收 + 告警人工（LLD §3.2），不发货、不建单
            return;
        }
        if (o.getAmount() != req.amount()) {
            throw new BizException(400, "PAY_AMOUNT_MISMATCH"); // 金额不符：告警人工，不发货
        }
        // 幂等：已处理状态不重复发货/改权益
        if ("paid".equals(o.getStatus()) || "activated".equals(o.getStatus()) || "refunded".equals(o.getStatus())) {
            return; // PAY_DUPLICATE
        }
        long now = System.currentTimeMillis();
        switch (req.tradeStatus()) {
            case "SUCCESS" -> { o.setStatus("activated"); o.setPaidAt(req.timestamp()); }
            case "CLOSED"  -> o.setStatus("closed");
            case "REFUND"  -> o.setStatus("refunded");
            default -> throw new BizException(400, "未知交易状态: " + req.tradeStatus());
        }
        orderRepo.save(o);
        // TODO: 发 C5 member.plan.changed 事件（权益激活），当前桩不接（payment LLD §8）
    }
}
