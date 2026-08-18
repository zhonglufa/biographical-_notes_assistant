package com.resumeai.module.interview.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/** A17 创建会话请求（对齐 interview-session-create.request）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SessionCreateRequest(String jobId, String mode, String questionSetId) {
}
