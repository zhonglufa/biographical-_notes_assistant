package com.resumeai.module.interview.dto;

import java.util.List;

/** A16 面试题集列表响应（对齐 interview-questions.response）。 */
public record QuestionSetsResponse(List<QuestionSetItem> questionSets) {
}
