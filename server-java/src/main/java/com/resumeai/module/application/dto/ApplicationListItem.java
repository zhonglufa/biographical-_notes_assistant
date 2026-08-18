package com.resumeai.module.application.dto;

/**
 * A10 投递列表项（对齐 implementation-index A10 applications-list.response）。
 */
public record ApplicationListItem(
        String id,
        String jobId,
        String platformId,
        String status,
        long updatedAt
) {
}
