package com.resumeai.module.resume.dto;

import java.util.List;

/** A05 响应（对齐 resume-versions.response.schema.json）：versions + diffAvailable。 */
public record ResumeVersionsResponse(List<ResumeVersionItem> versions, boolean diffAvailable) {
}
