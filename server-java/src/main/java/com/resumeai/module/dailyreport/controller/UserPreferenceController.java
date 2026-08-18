package com.resumeai.module.dailyreport.controller;

import com.resumeai.common.ApiResponse;
import com.resumeai.common.BizException;
import com.resumeai.module.dailyreport.dto.DailyReportPreferenceRequest;
import com.resumeai.module.dailyreport.dto.DailyReportPreferenceResponse;
import com.resumeai.module.dailyreport.service.DailyReportService;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/users")
public class UserPreferenceController {

    private final DailyReportService svc;

    public UserPreferenceController(DailyReportService svc) {
        this.svc = svc;
    }

    /** A25 更新日报推送偏好（路径在 /users 下，逻辑落在 dailyreport 模块）。 */
    @PutMapping("/daily-report/preference")
    public ApiResponse<DailyReportPreferenceResponse> update(
            @RequestHeader("Authorization") String auth,
            @RequestBody DailyReportPreferenceRequest req) {
        return ApiResponse.ok(svc.updatePreference(extractUserId(auth), req.pushTime(), req.enabled()));
    }

    private String extractUserId(String auth) {
        if (auth == null || !auth.startsWith("Bearer ")) throw new BizException(401, "未授权");
        return auth.substring("Bearer ".length());
    }
}
