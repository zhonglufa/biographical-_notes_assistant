package com.resumeai.module.dailyreport.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.resumeai.common.BizException;
import com.resumeai.module.dailyreport.dto.DailyReportPreferenceResponse;
import com.resumeai.module.dailyreport.dto.DailyReportStats;
import com.resumeai.module.dailyreport.dto.DailyReportTodayResponse;
import com.resumeai.module.dailyreport.dto.PlatformCount;
import com.resumeai.module.dailyreport.dto.TrendPoint;
import com.resumeai.module.dailyreport.entity.DailyReport;
import com.resumeai.module.dailyreport.entity.UserPreference;
import com.resumeai.module.dailyreport.repository.DailyReportRepository;
import com.resumeai.module.dailyreport.repository.UserPreferenceRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.regex.Pattern;

@Service
public class DailyReportServiceImpl implements DailyReportService {

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ISO_LOCAL_DATE;
    private static final Pattern PUSH_TIME = Pattern.compile("^([01]\\d|2[0-3]):[0-5]\\d$");
    private static final TypeReference<List<PlatformCount>> PLATFORM_LIST = new TypeReference<>() {};

    private final DailyReportRepository reportRepo;
    private final UserPreferenceRepository prefRepo;
    private final ObjectMapper mapper;

    public DailyReportServiceImpl(DailyReportRepository reportRepo,
                                  UserPreferenceRepository prefRepo,
                                  ObjectMapper mapper) {
        this.reportRepo = reportRepo;
        this.prefRepo = prefRepo;
        this.mapper = mapper;
    }

    /** 当前日期 yyyy-MM-dd（与实体 report_date 同格式）。包级可见便于测试对齐。 */
    static String today() {
        return LocalDate.now().format(DATE_FMT);
    }

    @Override
    public DailyReportTodayResponse getToday(String userId) {
        String date = today();
        DailyReport dr = reportRepo.findByUserIdAndReportDate(userId, date).orElse(null);
        if (dr == null) {
            return DailyReportTodayResponse.empty(date);
        }
        List<PlatformCount> byPlatform = parsePlatformBreakdown(dr.getPlatformBreakdown());
        List<TrendPoint> trend7d = reportRepo.findByUserIdOrderByReportDateDesc(userId, PageRequest.of(0, 7))
                .stream()
                .map(r -> new TrendPoint(r.getReportDate(), r.getTotalApplications()))
                .toList();
        DailyReportStats stats = new DailyReportStats(
                dr.getTotalApplications(), dr.getSuccessful(), dr.getFailed(), byPlatform,
                dr.getHrViews(), dr.getInterviewInvitations(), dr.getNewQuestions(), trend7d);
        return new DailyReportTodayResponse(date, buildSummary(dr), stats);
    }

    @Override
    public DailyReportPreferenceResponse updatePreference(String userId, String pushTime, boolean enabled) {
        if (pushTime == null || !PUSH_TIME.matcher(pushTime).matches()) {
            throw new BizException(400, "pushTime 格式非法，应为 HH:mm");
        }
        long now = System.currentTimeMillis();
        UserPreference up = prefRepo.findById(userId)
                .orElseGet(() -> new UserPreference(userId, pushTime, enabled));
        up.setDailyReportPushTime(pushTime);
        up.setDailyReportEnabled(enabled);
        up.setUpdatedAt(now);
        prefRepo.save(up);
        return new DailyReportPreferenceResponse(true, now);
    }

    /** 解析各平台分布；对 H2 JSON 列返回带引号字符串的坑做防御性二次解析（对齐 ResumeServiceImpl 处理）。 */
    private List<PlatformCount> parsePlatformBreakdown(String json) {
        if (json == null || json.isBlank()) {
            return List.of();
        }
        try {
            Object parsed = mapper.readValue(json, PLATFORM_LIST);
            if (parsed instanceof String s) {
                parsed = mapper.readValue(s, PLATFORM_LIST);
            }
            return (List<PlatformCount>) parsed;
        } catch (Exception e) {
            return List.of();
        }
    }

    private String buildSummary(DailyReport dr) {
        return String.format(
                "今日投递 %d 次（成功 %d / 失败 %d），HR 查看 %d 次，收到面试邀请 %d 个，新增面试题 %d 道。",
                dr.getTotalApplications(), dr.getSuccessful(), dr.getFailed(),
                dr.getHrViews(), dr.getInterviewInvitations(), dr.getNewQuestions());
    }
}
