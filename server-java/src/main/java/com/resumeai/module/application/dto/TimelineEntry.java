package com.resumeai.module.application.dto;

/**
 * A11 投递详情时间线条目（对齐 HLD §4.3 响应 {@code timeline:[{from,to,at,reason}]}）。
 * 数据源自 {@code application_event} 审计表。
 */
public record TimelineEntry(
        String from,
        String to,
        long at,
        String reason
) {
}
