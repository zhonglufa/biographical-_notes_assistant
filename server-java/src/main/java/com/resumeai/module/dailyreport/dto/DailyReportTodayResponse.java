package com.resumeai.module.dailyreport.dto;

import java.util.List;

/** A24 今日日报响应（对齐 daily-report-today.response）。无日报时返回空摘要，不报错（LLD §2 边界）。 */
public record DailyReportTodayResponse(String date, String summary, DailyReportStats stats) {
    public static DailyReportTodayResponse empty(String date) {
        DailyReportStats emptyStats = new DailyReportStats(
                0, 0, 0, List.of(), 0, 0, 0, List.of());
        return new DailyReportTodayResponse(date, "今日暂无投递活动", emptyStats);
    }
}
