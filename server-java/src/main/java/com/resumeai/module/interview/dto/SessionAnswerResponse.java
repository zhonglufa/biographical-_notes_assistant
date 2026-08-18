package com.resumeai.module.interview.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/** A18 提交作答响应（对齐 interview-session-answer.response）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SessionAnswerResponse(boolean accepted, Double score) {
}
