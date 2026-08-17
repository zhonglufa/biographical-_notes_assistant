package com.resumeai.module.resume.dto;

/** A04 响应（对齐 resumes-create.response.schema.json）：创建即落首个版本快照。 */
public record ResumeCreateResponse(String resumeId, String versionId, Long createdAt) {
}
