package com.resumeai.module.interview.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

/** A16 单题集条目（对齐 interview-questions.response）。 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record QuestionSetItem(String setId, String title, int questionCount, String difficulty, List<String> tags) {
}
