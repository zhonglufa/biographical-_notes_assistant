package com.resumeai.module.application.dto;

/**
 * A09 批量投递中被拒绝的岗位项（对齐 HLD §4.2 响应 {@code rejected:[{jobId,reason}]}）。
 */
public record BatchRejectItem(
        String jobId,
        String reason
) {
}
