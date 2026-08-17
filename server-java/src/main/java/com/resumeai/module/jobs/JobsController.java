package com.resumeai.module.jobs;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.jobs.dto.FavoriteRequest;
import com.resumeai.module.jobs.dto.FavoriteResponse;
import com.resumeai.module.jobs.dto.JobsListResponse;
import org.springframework.web.bind.annotation.*;

/**
 * 岗位浏览 REST 控制器（A07 / A08）。
 * 路径对齐 HLD §4.1：{@code /api/v1/jobs}、{@code /api/v1/jobs/{id}/favorite}。
 *
 * <p>鉴权简化同 P0：userId 从 Authorization 头占位解析（mock token，非真实 JWT）。</p>
 */
@RestController
@RequestMapping("/api/v1/jobs")
public class JobsController {

    private final JobsService svc;

    public JobsController(JobsService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<JobsListResponse> list(@RequestHeader("Authorization") String auth,
                                              @RequestParam(required = false) String keyword,
                                              @RequestParam(required = false) String location,
                                              @RequestParam(required = false) String platform,
                                              @RequestParam(required = false) Integer salaryMin,
                                              @RequestParam int page,
                                              @RequestParam int pageSize) {
        return ApiResponse.ok(svc.search(extractUserId(auth), keyword, location, platform, salaryMin, page, pageSize));
    }

    @PostMapping("/{id}/favorite")
    public ApiResponse<FavoriteResponse> favorite(@RequestHeader("Authorization") String auth,
                                                  @PathVariable String id,
                                                  @RequestBody FavoriteRequest req) {
        return ApiResponse.ok(svc.favorite(extractUserId(auth), id, req));
    }

    /** P0 占位解析：Bearer <token> → userId（TODO 接 JwtProperties 解析 subject）。 */
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
