package com.resumeai.module.notification.client;

import org.springframework.stereotype.Component;

import java.util.Base64;

/**
 * TODO: 真实签发一次性 WS token（过期需重连，HLD/通知 LLD §3.11）。
 * 当前内存桩：token 为 userId 的 URL-safe Base64，仅供编译与链路验证。
 */
@Component
public class InMemoryNotificationWsClient implements NotificationWsClient {
    @Override
    public String generateWsUrl(String userId) {
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(userId.getBytes());
        return "wss://notify.example.com/ws?token=" + token;
    }
}
