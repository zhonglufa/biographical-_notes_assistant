package com.resumeai.module.dailyreport.entity;
import com.baomidou.mybatisplus.annotation.*;

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
@TableName("daily_report")
@Getter
@Setter
@NoArgsConstructor
public class DailyReport {
    @TableId(type = IdType.INPUT)
    private String userId;

    // 复合主键第二列：MBP 不支持多 @TableId，降级为普通字段（仍由 Flyway 建复合 PK）。
    @TableField("report_date")
    private String reportDate;

    @TableField("total_applications")
    private int totalApplications;

    @TableField("successful")
    private int successful;

    @TableField("failed")
    private int failed;

    @TableField("hr_views")
    private int hrViews;

    @TableField("interview_invitations")
    private int interviewInvitations;

    @TableField("new_questions")
    private int newQuestions;

    /** 各平台投递分布，存为 JSON 字符串（TEXT）。 */
    @TableField("platform_breakdown")
    private String platformBreakdown;

    @TableField("sent_at")
    private Long sentAt;

    @TableField("created_at")
    private Long createdAt= System.currentTimeMillis();

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
