package com.resumeai.module.application.dto;

import java.util.List;

/**
 * A09 批量投递成功响应（202 Accepted · 对齐 HLD §4.2）。
 * <pre>{@code { batchId, accepted: 1..50, rejected: [{jobId, reason}] }}</pre>
 */
public record ApplyBatchResponse(
        String batchId,
        int accepted,
        List<BatchRejectItem> rejected
) {
}
