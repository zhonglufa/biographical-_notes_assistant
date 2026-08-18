package com.resumeai.module.interview.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

/** A19 评估报告响应（对齐 interview-session-report.response）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SessionReportResponse(String sessionId, int overallScore, List<Dimension> dimensions,
                                     Boolean degradeFlag, String feedback, Boolean appealEntry, Boolean rerunEntry) {
}
