package com.resumeai.module.dailyreport.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 每日日报快照（对齐 LLD-每日日报模块 §0–§2 + DB 设计 daily_report 表）。
 * 复合主键 (user_id, report_date)；每日每用户一条；trend7d 由历史行派生不落库。
 *
 * <p>约定（与团队已登记偏差一致）：
 * <ul>
 *   <li>user_id 用 VARCHAR(36) 与 Java String(36) 一致（DB LLD 写 BIGINT，偏差已登记）。</li>
 *   <li>时间戳用 BIGINT epoch 毫秒（与 notification 等模块一致，非 DATETIME）。</li>
 *   <li>platform_breakdown 存为 JSON 文本（TEXT），避免 H2/MySQL 间 JSON 列类型差异导致的解析坑。</li>
 * </ul>
 */
@Entity
@Table(name = "daily_report")
@IdClass(DailyReportId.class)
@Getter
@Setter
@NoArgsConstructor
public class DailyReport {
    @Id
    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Id
    @Column(name = "report_date", nullable = false, length = 10)
    private String reportDate;

    @Column(name = "total_applications", nullable = false)
    private int totalApplications;

    @Column(nullable = false)
    private int successful;

    @Column(nullable = false)
    private int failed;

    @Column(name = "hr_views", nullable = false)
    private int hrViews;

    @Column(name = "interview_invitations", nullable = false)
    private int interviewInvitations;

    @Column(name = "new_questions", nullable = false)
    private int newQuestions;

    /** 各平台投递分布，存为 JSON 字符串（TEXT）。 */
    @Column(name = "platform_breakdown", columnDefinition = "TEXT")
    private String platformBreakdown;

    @Column(name = "sent_at")
    private Long sentAt;

    @Column(name = "created_at", nullable = false)
    private Long createdAt = System.currentTimeMillis();

    public DailyReport(String userId, String reportDate, int totalApplications, int successful,
                       int failed, int hrViews, int interviewInvitations, int newQuestions,
                       String platformBreakdown) {
        this.userId = userId;
        this.reportDate = reportDate;
        this.totalApplications = totalApplications;
        this.successful = successful;
        this.failed = failed;
        this.hrViews = hrViews;
        this.interviewInvitations = interviewInvitations;
        this.newQuestions = newQuestions;
        this.platformBreakdown = platformBreakdown;
        this.createdAt = System.currentTimeMillis();
    }
}
