package com.resumeai.module.resume.dto;

/** A06 响应（对齐 resume-ats.response.schema.json）：异步触发，返回 taskId + 状态。 */
public record AtsScoreResponse(String taskId, String status) {
}
