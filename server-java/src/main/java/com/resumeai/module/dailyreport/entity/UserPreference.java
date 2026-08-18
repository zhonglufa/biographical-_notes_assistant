package com.resumeai.module.dailyreport.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 用户偏好（A25，对齐 LLD-每日日报模块 §4 + DB 设计 user_preference 表）。
 * 主键 user_id；日报推送时间 pushTime 存为 HH:mm 字符串（语义为"一天中的时刻"，非时间戳），与请求契约一致。
 * 与 strategy_config（投递策略）分离，避免偏好污染策略快照。
 */
@Entity
@Table(name = "user_preference")
@Getter
@Setter
@NoArgsConstructor
public class UserPreference {
    @Id
    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Column(name = "daily_report_push_time", nullable = false, length = 5)
    private String dailyReportPushTime;

    @Column(name = "daily_report_enabled", nullable = false)
    private boolean dailyReportEnabled;

    @Column(name = "created_at", nullable = false)
    private Long createdAt = System.currentTimeMillis();

    @Column(name = "updated_at", nullable = false)
    private Long updatedAt = System.currentTimeMillis();

    public UserPreference(String userId, String dailyReportPushTime, boolean dailyReportEnabled) {
        this.userId = userId;
        this.dailyReportPushTime = dailyReportPushTime;
        this.dailyReportEnabled = dailyReportEnabled;
        long now = System.currentTimeMillis();
        this.createdAt = now;
        this.updatedAt = now;
    }
}
