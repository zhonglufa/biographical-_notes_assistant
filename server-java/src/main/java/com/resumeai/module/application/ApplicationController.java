package com.resumeai.module.application;

import com.resumeai.module.application.dto.*;
import com.resumeai.module.application.service.ApplicationService;
import com.resumeai.security.SecurityContext;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 投递模块 REST 控制器（A09 / A10 / A11）。
 * 路径对齐 HLD §4.2/§4.3：{@code /api/v1/applications/batch}、{@code /applications}、{@code /applications/{id}}。
 *
 * <p>A09 成功响应为 202 Accepted（异步执行不阻塞）。</p>
 * <p>鉴权：userId 由 JwtAuthFilter 验签 RS256 JWT 后填充 SecurityContext；
 * A09 的「Bearer+role」日限额在业务层按角色强制（此处仅保证已认证）。</p>
 */
@RestController
@RequestMapping("/api/v1/applications")
public class ApplicationController {

    private final ApplicationService svc;

    public ApplicationController(ApplicationService svc) {
        this.svc = svc;
    }

    @PostMapping("/batch")
    public ResponseEntity<ApplyBatchResponse> batch(@RequestBody ApplyBatchRequest req) {
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(svc.applyBatch(SecurityContext.currentUserId(), req));
    }

    @GetMapping
    public ApplicationsListResponse list() {
        return svc.list(SecurityContext.currentUserId());
    }

    @GetMapping("/{id}")
    public ApplicationDetailResponse detail(@PathVariable String id) {
        return svc.detail(SecurityContext.currentUserId(), id);
    }
}
