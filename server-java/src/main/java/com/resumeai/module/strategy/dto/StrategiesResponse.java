package com.resumeai.module.strategy.dto;

import java.util.List;

/**
 * A12 读取策略配置 - 响应体（字段严格对齐 design/contracts/strategies.response.schema.json）。
 * 统一信封 data 内承载本对象。
 */
public record StrategiesResponse(
        double matchThreshold,
        int dailyLimit,
        List<String> platforms,
        List<String> blacklist
) {
}
