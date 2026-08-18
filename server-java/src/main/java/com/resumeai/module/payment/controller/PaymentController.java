package com.resumeai.module.payment.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.payment.dto.*;
import com.resumeai.module.payment.service.PaymentService;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    private final PaymentService svc;

    public PaymentController(PaymentService svc) {
        this.svc = svc;
    }

    @PostMapping("/orders")
    public ApiResponse<OrderCreateResponse> create(@RequestBody OrderCreateRequest req) {
        return ApiResponse.ok(svc.createOrder(SecurityContext.currentUserId(), req));
    }

    /** A21 渠道回调：渠道非对称签名验签（不用 Bearer），由 PaymentService 内部校验；不过 JWT 过滤器。 */
    @PostMapping("/callback")
    public ApiResponse<Void> callback(@RequestBody PaymentCallbackRequest req) {
        svc.handleCallback(req);
        return ApiResponse.ok(null);
    }
}
