package com.resumeai.module.interview.service;

import com.resumeai.common.BizException;
import com.resumeai.module.interview.client.InterviewAiClient;
import com.resumeai.module.interview.dto.*;
import com.resumeai.module.interview.entity.InterviewEvaluation;
import com.resumeai.module.interview.entity.InterviewSession;
import com.resumeai.module.interview.entity.InterviewSessionEvent;
import com.resumeai.module.interview.repository.InterviewEvaluationRepository;
import com.resumeai.module.interview.repository.InterviewSessionEventRepository;
import com.resumeai.module.interview.repository.InterviewSessionRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class InterviewServiceImpl implements InterviewService {

    private final InterviewSessionRepository sessionRepo;
    private final InterviewEvaluationRepository evaluationRepo;
    private final InterviewSessionEventRepository eventRepo;
    private final InterviewAiClient ai;

    public InterviewServiceImpl(InterviewSessionRepository sessionRepo,
                                InterviewEvaluationRepository evaluationRepo,
                                InterviewSessionEventRepository eventRepo,
                                InterviewAiClient ai) {
        this.sessionRepo = sessionRepo;
        this.evaluationRepo = evaluationRepo;
        this.eventRepo = eventRepo;
        this.ai = ai;
    }

    @Override
    public QuestionSetsResponse listQuestions(String userId) {
        // 题集由 Python B02 生成；此处内存桩数据（TODO 接真实生成）
        QuestionSetItem set1 = new QuestionSetItem("qset-backend", "后端工程师备战题集", 12, "medium",
                List.of("Java", "Spring", "分布式"));
        QuestionSetItem set2 = new QuestionSetItem("qset-frontend", "前端工程师备战题集", 10, "easy",
                List.of("Vue", "TypeScript"));
        return new QuestionSetsResponse(List.of(set1, set2));
    }

    @Override
    public SessionCreateResponse createSession(String userId, SessionCreateRequest req) {
        if (!"text".equals(req.mode()) && !"voice".equals(req.mode())) {
            throw new BizException(400, "mode 必须是 text 或 voice");
        }
        Long qsetId = req.questionSetId() != null ? Long.parseLong(req.questionSetId()) : ai.bootstrapQuestions(userId, req);
        InterviewSession s = new InterviewSession();
        s.setUserId(userId);
        s.setQuestionSetId(qsetId);
        if (req.jobId() != null) {
            try { s.setApplicationId(Long.parseLong(req.jobId())); } catch (NumberFormatException ignore) { /* 忽略非数字 */ }
        }
        s.setMode(req.mode());
        s.setState("created");
        s.setCurrentTurn(0);
        InterviewSession saved = sessionRepo.save(s);
        writeEvent(userId, saved.getId(), null, "created", "create_session"); // G7-1 审计
        return new SessionCreateResponse(String.valueOf(saved.getId()), saved.getState());
    }

    @Override
    public SessionAnswerResponse answer(String userId, String sessionId, SessionAnswerRequest req) {
        InterviewSession s = requireOwned(userId, sessionId);
        if (!"created".equals(s.getState()) && !"active".equals(s.getState()) && !"in_progress".equals(s.getState())) {
            throw new BizException(400, "会话当前状态(" + s.getState() + ")不可作答");
        }
        Double score = ai.evaluateAnswer(userId, s.getId(), req.questionId(), req.answer());
        int next = (s.getCurrentTurn() == null ? 0 : s.getCurrentTurn()) + 1;
        s.setCurrentTurn(next);
        if ("created".equals(s.getState()) || "active".equals(s.getState())) {
            writeEvent(userId, s.getId(), s.getState(), "in_progress", "first_answer");
            s.setState("in_progress");
        }
        sessionRepo.save(s);
        return new SessionAnswerResponse(true, score);
    }

    @Override
    public SessionReportResponse report(String userId, String sessionId) {
        InterviewSession s = requireOwned(userId, sessionId);
        InterviewEvaluation e = evaluationRepo.findBySessionId(s.getId())
                .orElseGet(() -> {
                    InterviewEvaluation gen = ai.evaluateSession(userId, s.getId());
                    gen.setCreatedAt(System.currentTimeMillis());
                    return evaluationRepo.save(gen);
                });
        if (!"completed".equals(s.getState()) && !"scored".equals(s.getState()) && !"abandoned".equals(s.getState())) {
            writeEvent(userId, s.getId(), s.getState(), "completed", "report");
            s.setState("completed");
            sessionRepo.save(s);
        }
        List<Dimension> dims = parseDimensions(e.getDimensions());
        return new SessionReportResponse(String.valueOf(s.getId()), e.getWeightedScore(), dims,
                e.isDegradeFlag(), "本次为 AI 模拟评估，仅供参考", e.isAppealEntry(), e.isRerunEntry());
    }

    private InterviewSession requireOwned(String userId, String sessionId) {
        Long id;
        try { id = Long.valueOf(sessionId); } catch (NumberFormatException ex) { throw new BizException(400, "sessionId 格式错误"); }
        return sessionRepo.findByUserIdAndId(userId, id)
                .orElseThrow(() -> new BizException(404, "会话不存在或不属于该用户"));
    }

    private void writeEvent(String userId, Long sessionId, String from, String to, String reason) {
        InterviewSessionEvent ev = new InterviewSessionEvent();
        ev.setUserId(userId);
        ev.setSessionId(sessionId);
        ev.setFromState(from);
        ev.setToState(to);
        ev.setReason(reason);
        ev.setActor("system");
        eventRepo.save(ev);
    }

    private List<Dimension> parseDimensions(String json) {
        // TODO: 真实应解析 e.getDimensions() JSON；内存桩返回固定 4 维（LLD G7-2 默认等权）
        return List.of(
                new Dimension("回答完整性", 4, "覆盖要点", null),
                new Dimension("技术准确性", 4, "技术正确", null),
                new Dimension("结构化表达", 3, "较清晰", null),
                new Dimension("与岗位匹配度", 4, "契合 JD", null)
        );
    }
}
