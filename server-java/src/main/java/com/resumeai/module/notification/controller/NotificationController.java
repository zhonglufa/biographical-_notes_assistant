package com.resumeai.module.notification.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.notification.dto.*;
import com.resumeai.module.notification.service.NotificationService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/notifications")
public class NotificationController {

    private final NotificationService svc;

    public NotificationController(NotificationService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<NotificationsListResponse> list(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(svc.list(extractUserId(auth)));
    }

    @GetMapping("/ws")
    public ApiResponse<WsUrlResponse> ws(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(svc.wsUrl(extractUserId(auth)));
    }

    private String extractUserId(String auth) {
        if (auth == null || !auth.startsWith("Bearer ")) throw new BizException(401, "未授权");
        return auth.substring("Bearer ".length());
    }
}
