package com.resumeai.module.strategy.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 策略配置实体（对齐 LLD-策略配置模块 §1 / LLD-数据库设计）。
 *
 * <p>每用户一行：{@code uk(user_id)}（HLD §3.5 / LLD §5）。
 * platforms/blacklist 为字符串数组，MySQL 存 JSON 文本（{@code platforms_json}/{@code blacklist_json}），
 * 由 Service 层用 Jackson 在 {@code List<String>} 与 JSON 间转换，避免 JPA 转换器在 H2 测试下的方言差异。</p>
 */
@TableName("strategy_config")
@Getter
@Setter
@NoArgsConstructor
public class StrategyConfig {

    @TableId(type = IdType.INPUT)
    private String userId;

    @TableField("match_threshold")
    private double matchThreshold;

    @TableField("daily_limit")
    private int dailyLimit;

    @TableField("platforms_json")
    private String platformsJson;

    @TableField("blacklist_json")
    private String blacklistJson;

    @TableField("updated_at")
    private Long updatedAt;
}
