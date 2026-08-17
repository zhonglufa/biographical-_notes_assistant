package com.resumeai.module.strategy.entity;

import jakarta.persistence.*;
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
@Entity
@Table(name = "strategy_config")
@Getter
@Setter
@NoArgsConstructor
public class StrategyConfig {

    @Id
    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Column(name = "match_threshold", nullable = false)
    private double matchThreshold;

    @Column(name = "daily_limit", nullable = false)
    private int dailyLimit;

    @Column(name = "platforms_json", length = 2000)
    private String platformsJson;

    @Column(name = "blacklist_json", length = 2000)
    private String blacklistJson;

    @Column(name = "updated_at", nullable = false)
    private Long updatedAt;
}
