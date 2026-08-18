package com.resumeai.module.payment.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.payment.dto.*;
import com.resumeai.module.payment.service.PaymentService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    private final PaymentService svc;

    public PaymentController(PaymentService svc) {
        this.svc = svc;
    }

    @PostMapping("/orders")
    public ApiResponse<OrderCreateResponse> create(@RequestHeader("Authorization") String auth,
                                                    @RequestBody OrderCreateRequest req) {
        return ApiResponse.ok(svc.createOrder(extractUserId(auth), req));
    }

    @PostMapping("/callback")
    public ApiResponse<Void> callback(@RequestBody PaymentCallbackRequest req) {
        svc.handleCallback(req);
        return ApiResponse.ok(null);
    }

    private String extractUserId(String auth) {
        if (auth == null || !auth.startsWith("Bearer ")) throw new BizException(401, "未授权");
        return auth.substring("Bearer ".length());
    }
}
