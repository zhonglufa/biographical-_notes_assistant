package com.resumeai.module.application;

import com.resumeai.common.BizException;
import com.resumeai.module.application.dto.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 投递模块 REST 控制器（A09 / A10 / A11）。
 * 路径对齐 HLD §4.2/§4.3：{@code /api/v1/applications/batch}、{@code /applications}、{@code /applications/{id}}。
 *
 * <p>P0 鉴权简化：userId 从 {@code Authorization} 头占位解析（mock token），
 * 非真实 RS256 JWT（TODO 接 JwtProperties / Security 过滤器，见 common 包）。</p>
 */
@RestController
@RequestMapping("/api/v1/applications")
public class ApplicationController {

    private final ApplicationService svc;

    public ApplicationController(ApplicationService svc) {
        this.svc = svc;
    }

    @PostMapping("/batch")
    public ResponseEntity<ApplyBatchResponse> batch(
            @RequestHeader("Authorization") String auth,
            @RequestBody ApplyBatchRequest req) {
        // A09 成功响应为 202 Accepted（异步执行不阻塞）
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(svc.applyBatch(extractUserId(auth), req));
    }

    @GetMapping
    public ApplicationsListResponse list(@RequestHeader("Authorization") String auth) {
        return svc.list(extractUserId(auth));
    }

    @GetMapping("/{id}")
    public ApplicationDetailResponse detail(
            @RequestHeader("Authorization") String auth,
            @PathVariable String id) {
        return svc.detail(extractUserId(auth), id);
    }

    /** P0 占位解析：Bearer <token> → userId；非 JWT 验签（TODO 真实鉴权）。 */
    private String extractUserId(String auth) {
        if (auth == null || auth.isBlank()) {
            throw new BizException(401, "UNAUTHORIZED");
        }
        String token = auth.startsWith("Bearer ") ? auth.substring(7) : auth;
        if (token.isBlank()) {
            throw new BizException(401, "UNAUTHORIZED");
        }
        return "u-" + token; // 占位 userId（TODO 接 JwtProperties 解析 subject）
    }
}
