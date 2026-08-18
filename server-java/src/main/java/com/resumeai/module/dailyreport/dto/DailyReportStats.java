package com.resumeai.module.dailyreport.dto;

import java.util.List;

/** A24 今日日报统计（对齐 daily-report-today.response.stats）。 */
public record DailyReportStats(
        int appliedTotal,
        int success,
        int failed,
        List<PlatformCount> byPlatform,
        int hrViews,
        int interviewInvites,
        int newQuestions,
        List<TrendPoint> trend7d) {
}
