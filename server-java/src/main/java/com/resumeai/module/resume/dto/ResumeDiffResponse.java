package com.resumeai.module.resume.dto;

import java.util.List;

/** A05 diff 响应（对齐 resume-diff.response.schema.json）：changes[] + generatedAt。 */
public record ResumeDiffResponse(List<ResumeDiffChange> changes, Long generatedAt) {
}
