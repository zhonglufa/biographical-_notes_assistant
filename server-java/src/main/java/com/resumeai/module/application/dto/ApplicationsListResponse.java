package com.resumeai.module.application.dto;

import java.util.List;

/**
 * A10 投递列表响应（对齐 implementation-index A10 applications-list.response）。
 */
public record ApplicationsListResponse(
        List<ApplicationListItem> items,
        long total
) {
}
