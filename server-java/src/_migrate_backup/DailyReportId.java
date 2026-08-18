package com.resumeai.module.dailyreport.entity;

import java.io.Serializable;
import java.util.Objects;

/**
 * 日报复合主键（user_id + report_date）。
 * 对齐 DB 设计 daily_report 表：每日每用户一条，以 (user_id, report_date) 唯一定位。
 */
public class DailyReportId implements Serializable {
    private String userId;
    private String reportDate;

    public DailyReportId() {
    }

    public DailyReportId(String userId, String reportDate) {
        this.userId = userId;
        this.reportDate = reportDate;
    }

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getReportDate() {
        return reportDate;
    }

    public void setReportDate(String reportDate) {
        this.reportDate = reportDate;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof DailyReportId)) return false;
        DailyReportId that = (DailyReportId) o;
        return Objects.equals(userId, that.userId) && Objects.equals(reportDate, that.reportDate);
    }

    @Override
    public int hashCode() {
        return Objects.hash(userId, reportDate);
    }
}
