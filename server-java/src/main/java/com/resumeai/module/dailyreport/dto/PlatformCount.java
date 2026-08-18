package com.resumeai.module.dailyreport.dto;

/** 各平台投递分布项（对齐 daily-report-today.response.stats.byPlatform）。 */
public record PlatformCount(String platformId, int count) {
}
