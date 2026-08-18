package com.resumeai.module.adapter;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.adapter.dto.AdapterEnableRequest;
import com.resumeai.module.adapter.dto.AdapterEnableResponse;
import com.resumeai.module.adapter.dto.AdaptersListResponse;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

/**
 * 适配器编排 REST 控制器（A14 / A15）。
 * 路径对齐 HLD §4.1：{@code /api/v1/adapters}、{@code /api/v1/adapters/{id}/enable}。
 *
 * <p>红线：本控制器只做编排（元数据 + 启停态 + 下发 Agent 指令），不触达平台、不处理 Cookie。</p>
 * <p>鉴权：userId 由 JwtAuthFilter 验签 RS256 JWT 后填充 SecurityContext（A15 还需 pro+ 套餐，
 * 由 PermissionInterceptor 强制）。</p>
 */
@RestController
@RequestMapping("/api/v1/adapters")
public class AdapterController {

    private final AdapterService svc;

    public AdapterController(AdapterService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<AdaptersListResponse> list() {
        return ApiResponse.ok(svc.list(SecurityContext.currentUserId()));
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<AdapterEnableResponse> enable(@PathVariable String id,
                                                     @RequestBody AdapterEnableRequest req) {
        return ApiResponse.ok(svc.enable(SecurityContext.currentUserId(), id, req.enabled()));
    }
}
