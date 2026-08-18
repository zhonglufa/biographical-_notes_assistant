package com.resumeai.module.notification.service;

import com.resumeai.module.notification.dto.*;

public interface NotificationService {
    /** A22 通知列表（含未读计数，按 userId 隔离）。 */
    NotificationsListResponse list(String userId);

    /** A23 返回已签名的 WebSocket 连接地址。 */
    WsUrlResponse wsUrl(String userId);
}
