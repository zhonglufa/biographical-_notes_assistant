package com.resumeai.module.dailyreport.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.dailyreport.dto.DailyReportTodayResponse;
import com.resumeai.module.dailyreport.service.DailyReportService;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/daily-report")
public class DailyReportController {

    private final DailyReportService svc;

    public DailyReportController(DailyReportService svc) {
        this.svc = svc;
    }

    /** A24 今日日报（userId 由 JwtAuthFilter 验签后填充 SecurityContext）。 */
    @GetMapping("/today")
    public ApiResponse<DailyReportTodayResponse> today() {
        return ApiResponse.ok(svc.getToday(SecurityContext.currentUserId()));
    }
}
