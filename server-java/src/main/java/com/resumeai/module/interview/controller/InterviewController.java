package com.resumeai.module.interview.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.interview.dto.*;
import com.resumeai.module.interview.service.InterviewService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/interviews")
public class InterviewController {

    private final InterviewService svc;

    public InterviewController(InterviewService svc) {
        this.svc = svc;
    }

    @GetMapping("/questions")
    public ApiResponse<QuestionSetsResponse> questions(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(svc.listQuestions(extractUserId(auth)));
    }

    @PostMapping("/sessions")
    public ApiResponse<SessionCreateResponse> create(@RequestHeader("Authorization") String auth,
                                                      @RequestBody SessionCreateRequest req) {
        return ApiResponse.ok(svc.createSession(extractUserId(auth), req));
    }

    @PostMapping("/sessions/{id}/answer")
    public ApiResponse<SessionAnswerResponse> answer(@RequestHeader("Authorization") String auth,
                                                      @PathVariable String id,
                                                      @RequestBody SessionAnswerRequest req) {
        return ApiResponse.ok(svc.answer(extractUserId(auth), id, req));
    }

    @GetMapping("/sessions/{id}/report")
    public ApiResponse<SessionReportResponse> report(@RequestHeader("Authorization") String auth,
                                                     @PathVariable String id) {
        return ApiResponse.ok(svc.report(extractUserId(auth), id));
    }

    private String extractUserId(String auth) {
        if (auth == null || !auth.startsWith("Bearer ")) throw new BizException(401, "未授权");
        return auth.substring("Bearer ".length());
    }
}
