package com.resumeai.module.interview.dto;

import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * A18 提交作答请求（对齐 interview-session-answer.request）。
 * answer 为 oneOf：文本(String) 或 {audioRef:String}（语音引用），用 Object 兼容两种形态。
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SessionAnswerRequest(String questionId, Object answer, String asrProvider) {
}
