package com.resumeai.module.jobs;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.jobs.dto.FavoriteRequest;
import com.resumeai.module.jobs.dto.FavoriteResponse;
import com.resumeai.module.jobs.dto.JobsListResponse;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

/**
 * 岗位浏览 REST 控制器（A07 / A08）。
 * 路径对齐 HLD §4.1：{@code /api/v1/jobs}、{@code /api/v1/jobs/{id}/favorite}。
 *
 * <p>鉴权：userId 由 JwtAuthFilter 验签 RS256 JWT 后填充 SecurityContext。</p>
 */
@RestController
@RequestMapping("/api/v1/jobs")
public class JobsController {

    private final JobsService svc;

    public JobsController(JobsService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<JobsListResponse> list(
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String location,
            @RequestParam(required = false) String platform,
            @RequestParam(required = false) Integer salaryMin,
            @RequestParam int page,
            @RequestParam int pageSize) {
        return ApiResponse.ok(svc.search(SecurityContext.currentUserId(), keyword, location, platform, salaryMin, page, pageSize));
    }

    @PostMapping("/{id}/favorite")
    public ApiResponse<FavoriteResponse> favorite(@PathVariable String id,
                                                  @RequestBody FavoriteRequest req) {
        return ApiResponse.ok(svc.favorite(SecurityContext.currentUserId(), id, req));
    }
}
