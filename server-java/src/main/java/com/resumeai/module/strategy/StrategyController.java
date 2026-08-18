package com.resumeai.module.strategy;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.strategy.dto.StrategiesRequest;
import com.resumeai.module.strategy.dto.StrategiesResponse;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

/**
 * 策略配置 REST 控制器（A12 / A13 · 对齐 implementation-index.md）。
 * 路径：{@code GET|PUT /api/v1/strategies}。
 *
 * <p>鉴权：userId 由 JwtAuthFilter 验签 RS256 JWT 后填充 SecurityContext；
 * A13（PUT，auth=Bearer+pro）还需 pro+ 套餐，由 PermissionInterceptor 强制。</p>
 */
@RestController
@RequestMapping("/api/v1/strategies")
public class StrategyController {

    private final StrategyService svc;

    public StrategyController(StrategyService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<StrategiesResponse> get() {
        return ApiResponse.ok(svc.get(SecurityContext.currentUserId()));
    }

    @PutMapping
    public ApiResponse<StrategiesResponse> save(@RequestBody StrategiesRequest req) {
        return ApiResponse.ok(svc.save(SecurityContext.currentUserId(), req));
    }
}
