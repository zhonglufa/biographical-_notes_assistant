package com.resumeai.module.adapter;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.adapter.dto.AdapterEnableRequest;
import com.resumeai.module.adapter.dto.AdapterEnableResponse;
import com.resumeai.module.adapter.dto.AdaptersListResponse;
import org.springframework.web.bind.annotation.*;

/**
 * 适配器编排 REST 控制器（A14 / A15）。
 * 路径对齐 HLD §4.1：{@code /api/v1/adapters}、{@code /api/v1/adapters/{id}/enable}。
 *
 * <p>红线：本控制器只做编排（元数据 + 启停态 + 下发 Agent 指令），不触达平台、不处理 Cookie。</p>
 */
@RestController
@RequestMapping("/api/v1/adapters")
public class AdapterController {

    private final AdapterService svc;

    public AdapterController(AdapterService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<AdaptersListResponse> list(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(svc.list(extractUserId(auth)));
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<AdapterEnableResponse> enable(@RequestHeader("Authorization") String auth,
                                                     @PathVariable String id,
                                                     @RequestBody AdapterEnableRequest req) {
        return ApiResponse.ok(svc.enable(extractUserId(auth), id, req.enabled()));
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
