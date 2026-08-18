package com.resumeai.module.notification.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.notification.dto.NotificationsListResponse;
import com.resumeai.module.notification.dto.WsUrlResponse;
import com.resumeai.module.notification.service.NotificationService;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/notifications")
public class NotificationController {

    private final NotificationService svc;

    public NotificationController(NotificationService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<NotificationsListResponse> list() {
        return ApiResponse.ok(svc.list(SecurityContext.currentUserId()));
    }

    /** A23 WebSocket 连接地址（auth=Bearer(query)，令牌由 JwtAuthFilter 从 ?token= 读取）。 */
    @GetMapping("/ws")
    public ApiResponse<WsUrlResponse> ws() {
        return ApiResponse.ok(svc.wsUrl(SecurityContext.currentUserId()));
    }
}
