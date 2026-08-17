package com.resumeai.module.resume;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.resume.dto.AtsScoreRequest;
import com.resumeai.module.resume.dto.AtsScoreResponse;
import com.resumeai.module.resume.dto.ResumeCreateRequest;
import com.resumeai.module.resume.dto.ResumeCreateResponse;
import com.resumeai.module.resume.dto.ResumeDiffRequest;
import com.resumeai.module.resume.dto.ResumeDiffResponse;
import com.resumeai.module.resume.dto.ResumeVersionsResponse;
import org.springframework.web.bind.annotation.*;

/**
 * 简历工作台 REST 控制器（A04 / A05 / A06）。
 * 路径对齐 HLD §4.1：{@code /api/v1/resumes}、{@code /resumes/{id}/versions}、
 * {@code /resumes/{id}/diff}、{@code /resumes/ats-score}。
 *
 * <p>边界：不调 LLM 润色、不管理模板 CSS（LLD §0）。</p>
 */
@RestController
@RequestMapping("/api/v1/resumes")
public class ResumeController {

    private final ResumeService svc;

    public ResumeController(ResumeService svc) {
        this.svc = svc;
    }

    @PostMapping
    public ApiResponse<ResumeCreateResponse> create(@RequestHeader("Authorization") String auth,
                                                    @RequestBody ResumeCreateRequest req) {
        return ApiResponse.ok(svc.create(extractUserId(auth), req));
    }

    @GetMapping("/{id}/versions")
    public ApiResponse<ResumeVersionsResponse> versions(@RequestHeader("Authorization") String auth,
                                                        @PathVariable String id) {
        return ApiResponse.ok(svc.listVersions(extractUserId(auth), id));
    }

    @PostMapping("/{id}/diff")
    public ApiResponse<ResumeDiffResponse> diff(@RequestHeader("Authorization") String auth,
                                                @PathVariable String id,
                                                @RequestBody ResumeDiffRequest req) {
        return ApiResponse.ok(svc.diff(extractUserId(auth), id, req));
    }

    @PostMapping("/ats-score")
    public ApiResponse<AtsScoreResponse> atsScore(@RequestHeader("Authorization") String auth,
                                                  @RequestBody AtsScoreRequest req) {
        return ApiResponse.ok(svc.atsScore(extractUserId(auth), req));
    }

    private String extractUserId(String auth) {
        if (auth == null || auth.isBlank()) {
            throw new BizException(401, "UNAUTHORIZED");
        }
        String token = auth.startsWith("Bearer ") ? auth.substring(7) : auth;
        if (token.isBlank()) {
            throw new BizException(401, "UNAUTHORIZED");
        }
        return "u-" + token;
    }
}
