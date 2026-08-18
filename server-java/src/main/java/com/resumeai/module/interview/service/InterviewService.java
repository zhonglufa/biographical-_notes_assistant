package com.resumeai.module.interview.service;

import com.resumeai.module.interview.dto.*;

public interface InterviewService {
    /** A16 面试题集列表（备战）。 */
    QuestionSetsResponse listQuestions(String userId);

    /** A17 创建 AI 面试会话。 */
    SessionCreateResponse createSession(String userId, SessionCreateRequest req);

    /** A18 提交作答（驱动 B03 评估）。 */
    SessionAnswerResponse answer(String userId, String sessionId, SessionAnswerRequest req);

    /** A19 评估报告（含重跑/申诉入口）。 */
    SessionReportResponse report(String userId, String sessionId);
}
