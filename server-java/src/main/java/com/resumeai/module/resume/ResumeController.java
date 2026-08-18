package com.resumeai.module.resume;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.resume.dto.AtsScoreRequest;
import com.resumeai.module.resume.dto.AtsScoreResponse;
import com.resumeai.module.resume.dto.ResumeCreateRequest;
import com.resumeai.module.resume.dto.ResumeCreateResponse;
import com.resumeai.module.resume.dto.ResumeDiffRequest;
import com.resumeai.module.resume.dto.ResumeDiffResponse;
import com.resumeai.module.resume.dto.ResumeVersionsResponse;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

/**
 * 简历工作台 REST 控制器（A04 / A05 / A06）。
 * 路径对齐 HLD §4.1：{@code /api/v1/resumes}、{@code /resumes/{id}/versions}、
 * {@code /resumes/{id}/diff}、{@code /resumes/ats-score}。
 *
 * <p>边界：不调 LLM 润色、不管理模板 CSS（LLD §0）。</p>
 * <p>鉴权：userId 由 JwtAuthFilter 验签 RS256 JWT 后填充 SecurityContext。</p>
 */
@RestController
@RequestMapping("/api/v1/resumes")
public class ResumeController {

    private final ResumeService svc;

    public ResumeController(ResumeService svc) {
        this.svc = svc;
    }

    @PostMapping
    public ApiResponse<ResumeCreateResponse> create(@RequestBody ResumeCreateRequest req) {
        return ApiResponse.ok(svc.create(SecurityContext.currentUserId(), req));
    }

    @GetMapping("/{id}/versions")
    public ApiResponse<ResumeVersionsResponse> versions(@PathVariable String id) {
        return ApiResponse.ok(svc.listVersions(SecurityContext.currentUserId(), id));
    }

    @PostMapping("/{id}/diff")
    public ApiResponse<ResumeDiffResponse> diff(@PathVariable String id,
                                                @RequestBody ResumeDiffRequest req) {
        return ApiResponse.ok(svc.diff(SecurityContext.currentUserId(), id, req));
    }

    @PostMapping("/ats-score")
    public ApiResponse<AtsScoreResponse> atsScore(@RequestBody AtsScoreRequest req) {
        return ApiResponse.ok(svc.atsScore(SecurityContext.currentUserId(), req));
    }
}
