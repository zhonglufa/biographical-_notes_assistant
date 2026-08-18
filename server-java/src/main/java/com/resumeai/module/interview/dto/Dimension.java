package com.resumeai.module.interview.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/** A19 评估维度（对齐 interview-session-report.response.dimensions）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Dimension(String dim, int rawScore, String reason, Double score) {
}
