package com.resumeai.module.resume.dto;

/** A05 diff 单项（对齐 resume-diff.response.schema.json）：field / op / from / to。 */
public record ResumeDiffChange(String field, String op, String from, String to) {
}
