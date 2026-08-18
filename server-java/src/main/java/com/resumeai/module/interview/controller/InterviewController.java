package com.resumeai.module.interview.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.interview.dto.*;
import com.resumeai.module.interview.service.InterviewService;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/interviews")
public class InterviewController {

    private final InterviewService svc;

    public InterviewController(InterviewService svc) {
        this.svc = svc;
    }

    @GetMapping("/questions")
    public ApiResponse<QuestionSetsResponse> questions() {
        return ApiResponse.ok(svc.listQuestions(SecurityContext.currentUserId()));
    }

    @PostMapping("/sessions")
    public ApiResponse<SessionCreateResponse> create(@RequestBody SessionCreateRequest req) {
        return ApiResponse.ok(svc.createSession(SecurityContext.currentUserId(), req));
    }

    @PostMapping("/sessions/{id}/answer")
    public ApiResponse<SessionAnswerResponse> answer(@PathVariable String id,
                                                     @RequestBody SessionAnswerRequest req) {
        return ApiResponse.ok(svc.answer(SecurityContext.currentUserId(), id, req));
    }

    @GetMapping("/sessions/{id}/report")
    public ApiResponse<SessionReportResponse> report(@PathVariable String id) {
        return ApiResponse.ok(svc.report(SecurityContext.currentUserId(), id));
    }
}
