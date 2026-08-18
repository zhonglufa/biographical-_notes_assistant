package com.resumeai.module.notification.client;

/** 通知 WebSocket 门面（A23 签发一次性连接地址，auth=Bearer(query)）。 */
public interface NotificationWsClient {
    String generateWsUrl(String userId);
}
