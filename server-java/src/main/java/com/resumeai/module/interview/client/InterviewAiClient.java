package com.resumeai.module.interview.client;

import com.resumeai.module.interview.dto.SessionCreateRequest;
import com.resumeai.module.interview.entity.InterviewEvaluation;

/**
 * 面试智能层门面（对齐 LLD §2 InterviewSessionFacade 6 方法）。
 * 真实实现应调 Python B02/B03（LLM 出题/评估）；当前由内存 stub 替代（见 InMemoryInterviewAiClient）。
 */
public interface InterviewAiClient {
    /** 触发 AI 生成题集/首题（B02），返回题集 id（占位）。 */
    Long bootstrapQuestions(String userId, SessionCreateRequest req);

    /** 逐轮评估（B03），返回 turnScore(0..1)。 */
    Double evaluateAnswer(String userId, Long sessionId, String questionId, Object answer);

    /** 综合评估（B03 聚合），返回报告实体（未持久化）。 */
    InterviewEvaluation evaluateSession(String userId, Long sessionId);
}
