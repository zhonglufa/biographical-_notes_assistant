package com.resumeai.module.dailyreport.dto;

/** 近 7 天趋势点（对齐 daily-report-today.response.stats.trend7d）。 */
public record TrendPoint(String date, int count) {
}
