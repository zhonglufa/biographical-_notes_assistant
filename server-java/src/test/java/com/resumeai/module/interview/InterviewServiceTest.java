package com.resumeai.module.interview;

import com.resumeai.common.BizException;
import com.resumeai.module.interview.dto.*;
import com.resumeai.module.interview.service.InterviewService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

/** A16/A17/A18/A19 关键路径单测（H2 内存库 · 对齐 P0/P1 范式）。 */
@SpringBootTest
@ActiveProfiles("test")
class InterviewServiceTest {

    @Autowired
    private InterviewService svc;

    @Test
    void 题集列表_返回非空() {
        QuestionSetsResponse r = svc.listQuestions("u-1");
        assertFalse(r.questionSets().isEmpty());
    }

    @Test
    void 创建会话_返回created状态() {
        SessionCreateResponse r = svc.createSession("u-1", new SessionCreateRequest(null, "text", null));
        assertNotNull(r.sessionId());
        assertEquals("created", r.status());
    }

    @Test
    void 非法mode_抛400() {
        BizException ex = assertThrows(BizException.class,
                () -> svc.createSession("u-1", new SessionCreateRequest(null, "fax", null)));
        assertEquals(400, ex.getCode());
    }

    @Test
    void 作答_返回accepted与score() {
        SessionCreateResponse c = svc.createSession("u-2", new SessionCreateRequest(null, "text", null));
        SessionAnswerResponse a = svc.answer("u-2", c.sessionId(), new SessionAnswerRequest("q1", "我的回答", null));
        assertTrue(a.accepted());
        assertNotNull(a.score());
    }

    @Test
    void 报告_返回综合分与维度() {
        SessionCreateResponse c = svc.createSession("u-3", new SessionCreateRequest(null, "text", null));
        svc.answer("u-3", c.sessionId(), new SessionAnswerRequest("q1", "回答内容", null));
        SessionReportResponse r = svc.report("u-3", c.sessionId());
        assertTrue(r.overallScore() >= 0 && r.overallScore() <= 100);
        assertFalse(r.dimensions().isEmpty());
    }

    @Test
    void 他人会话_报告404不泄露() {
        SessionCreateResponse c = svc.createSession("u-owner", new SessionCreateRequest(null, "text", null));
        BizException ex = assertThrows(BizException.class, () -> svc.report("u-stranger", c.sessionId()));
        assertEquals(404, ex.getCode());
    }
}
