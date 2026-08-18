package com.resumeai.module.dailyreport.service;

import com.resumeai.module.dailyreport.dto.DailyReportPreferenceResponse;
import com.resumeai.module.dailyreport.dto.DailyReportTodayResponse;

public interface DailyReportService {
    /** A24 今日日报：读取预聚合的 daily_report 行；无则返空摘要，不抛错（LLD §2）。 */
    DailyReportTodayResponse getToday(String userId);

    /** A25 更新日报推送偏好（upsert user_preference）。 */
    DailyReportPreferenceResponse updatePreference(String userId, String pushTime, boolean enabled);
}
