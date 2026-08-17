package com.resumeai.module.strategy.dto;

import java.util.List;

/**
 * A13 更新策略配置 - 请求体（字段严格对齐 design/contracts/strategies.request.schema.json）。
 * <ul>
 *   <li>matchThreshold: 匹配阈值 0..1；</li>
 *   <li>dailyLimit: 每日投递上限（免费 30 / 专业·高级 100）；</li>
 *   <li>platforms: 启用平台白名单；</li>
 *   <li>blacklist: 屏蔽企业/岗位关键字。</li>
 * </ul>
 */
public record StrategiesRequest(
        double matchThreshold,
        int dailyLimit,
        List<String> platforms,
        List<String> blacklist
) {
}
