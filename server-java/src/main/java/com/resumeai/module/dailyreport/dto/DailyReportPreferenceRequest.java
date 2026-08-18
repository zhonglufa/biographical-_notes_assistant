package com.resumeai.module.dailyreport.dto;

/** A25 日报推送偏好请求（对齐 daily-report-preference.request）。 */
public record DailyReportPreferenceRequest(String pushTime, boolean enabled) {
}
