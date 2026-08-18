package com.resumeai.module.dailyreport.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.dailyreport.dto.DailyReportTodayResponse;
import com.resumeai.module.dailyreport.service.DailyReportService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/daily-report")
public class DailyReportController {

    private final DailyReportService svc;

    public DailyReportController(DailyReportService svc) {
        this.svc = svc;
    }

    /** A24 今日日报（Bearer 头携带 userId；与团队占位鉴权约定一致）。 */
    @GetMapping("/today")
    public ApiResponse<DailyReportTodayResponse> today(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(svc.getToday(extractUserId(auth)));
    }

    private String extractUserId(String auth) {
        if (auth == null || !auth.startsWith("Bearer ")) throw new BizException(401, "未授权");
        return auth.substring("Bearer ".length());
    }
}
