package com.resumeai.module.notification.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/** A22 单条通知（对齐 notifications-list.response.items）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record NotificationItem(String id, String level, String title, String body, boolean read, Long createdAt, String channel) {
}
