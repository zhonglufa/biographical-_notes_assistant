package com.resumeai.module.strategy;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.strategy.dto.StrategiesRequest;
import com.resumeai.module.strategy.dto.StrategiesResponse;
import org.springframework.web.bind.annotation.*;

/**
 * 策略配置 REST 控制器（A12 / A13 · 对齐 implementation-index.md）。
 * 路径：{@code GET|PUT /api/v1/strategies}。
 *
 * <p>P0 鉴权简化：userId 从 {@code Authorization} 头占位解析（mock token），非真实 RS256 JWT（TODO）。</p>
 */
@RestController
@RequestMapping("/api/v1/strategies")
public class StrategyController {

    private final StrategyService svc;

    public StrategyController(StrategyService svc) {
        this.svc = svc;
    }

    @GetMapping
    public ApiResponse<StrategiesResponse> get(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(svc.get(extractUserId(auth)));
    }

    @PutMapping
    public ApiResponse<StrategiesResponse> save(
            @RequestHeader("Authorization") String auth,
            @RequestBody StrategiesRequest req) {
        return ApiResponse.ok(svc.save(extractUserId(auth), req));
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
