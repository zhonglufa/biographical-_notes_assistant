package com.resumeai.module.interview.client;

import com.resumeai.module.interview.dto.SessionCreateRequest;
import com.resumeai.module.interview.entity.InterviewEvaluation;
import org.springframework.stereotype.Component;

import java.util.Random;

/**
 * TODO: 接 Python B02/B03（LLM 出题/评估）。当前内存桩：生成假题集、固定分段、假报告，
 * 仅供编译与链路验证，不进入生产评估逻辑。
 */
@Component
public class InMemoryInterviewAiClient implements InterviewAiClient {
    private final Random rnd = new Random();

    @Override
    public Long bootstrapQuestions(String userId, SessionCreateRequest req) {
        return Math.abs(rnd.nextLong() % 100000) + 1;
    }

    @Override
    public Double evaluateAnswer(String userId, Long sessionId, String questionId, Object answer) {
        return 0.6 + rnd.nextDouble() * 0.4; // 0.6~1.0
    }

    @Override
    public InterviewEvaluation evaluateSession(String userId, Long sessionId) {
        InterviewEvaluation e = new InterviewEvaluation();
        e.setSessionId(sessionId);
        e.setWeightedScore(72 + rnd.nextInt(20)); // 72~91
        // 4 维等权（LLD T2/T3 默认）
        e.setDimensions("[{\"dim\":\"回答完整性\",\"rawScore\":4,\"reason\":\"覆盖要点\"},"
                + "{\"dim\":\"技术准确性\",\"rawScore\":4,\"reason\":\"技术正确\"},"
                + "{\"dim\":\"结构化表达\",\"rawScore\":3,\"reason\":\"较清晰\"},"
                + "{\"dim\":\"与岗位匹配度\",\"rawScore\":4,\"reason\":\"契合 JD\"}]");
        e.setDegradeFlag(false);
        e.setAppealEntry(true);
        e.setRerunEntry(true);
        return e;
    }
}
