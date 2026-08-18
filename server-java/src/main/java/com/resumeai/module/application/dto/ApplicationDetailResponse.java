package com.resumeai.module.application.dto;

import java.util.List;

/**
 * A11 投递详情响应（对齐 HLD §4.3）。
 * <pre>{@code { id, jobId, platformId, status, timeline:[{from,to,at,reason}], evidence? }}</pre>
 * 状态枚举：pending_confirm/autofilling/submitted/viewed/contacting/interview_invited/
 * interview_done/offer/rejected/closed。evidence 为可选证据引用（如 viewed 快照 url）。
 */
public record ApplicationDetailResponse(
        String id,
        String jobId,
        String platformId,
        String status,
        List<TimelineEntry> timeline,
        String evidence
) {
}
