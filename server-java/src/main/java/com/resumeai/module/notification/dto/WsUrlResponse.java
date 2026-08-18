package com.resumeai.module.notification.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/** A23 WebSocket 连接响应（对齐 notification-ws.response）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record WsUrlResponse(String wsUrl, Integer expiresIn) {
}
