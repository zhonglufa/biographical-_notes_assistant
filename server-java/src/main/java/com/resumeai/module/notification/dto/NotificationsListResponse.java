package com.resumeai.module.notification.dto;

import java.util.List;

/** A22 通知列表响应（对齐 notifications-list.response）。 */
public record NotificationsListResponse(List<NotificationItem> items, int unread) {
}
