package com.resumeai.module.resume.dto;

/** A05 版本列表单项（对齐 resume-versions.response.schema.json）。 */
public record ResumeVersionItem(String versionId, int versionNo, Long createdAt, String note, boolean isPreferred) {
}
