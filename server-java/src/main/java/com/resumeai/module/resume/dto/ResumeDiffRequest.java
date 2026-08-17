package com.resumeai.module.resume.dto;

/** A05 diff 请求（对齐 resume-diff.request.schema.json）：指定两版本做字段级结构化 diff。 */
public record ResumeDiffRequest(String fromVersionId, String toVersionId) {
}
