package com.resumeai.module.resume.dto;

/** A04 请求（对齐 resumes-create.request.schema.json）：title + 结构化简历 content + 可选 templateId。 */
public record ResumeCreateRequest(String title, Object content, String templateId) {
}
