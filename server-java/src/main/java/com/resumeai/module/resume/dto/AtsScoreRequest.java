package com.resumeai.module.resume.dto;

/** A06 请求（对齐 resume-ats.request.schema.json）：锁版本触发 ATS 评分。 */
public record AtsScoreRequest(String resumeVersionId) {
}
