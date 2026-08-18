package com.resumeai.module.dailyreport;

import com.resumeai.common.BizException;
import com.resumeai.module.dailyreport.dto.DailyReportPreferenceResponse;
import com.resumeai.module.dailyreport.dto.DailyReportTodayResponse;
import com.resumeai.module.dailyreport.entity.DailyReport;
import com.resumeai.module.dailyreport.entity.UserPreference;
import com.resumeai.module.dailyreport.repository.DailyReportRepository;
import com.resumeai.module.dailyreport.repository.UserPreferenceRepository;
import com.resumeai.module.dailyreport.service.DailyReportService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

import static org.junit.jupiter.api.Assertions.*;

/** A24/A25 关键路径单测（H2 内存库 · 对齐 P2 范式：@Transactional 隔离每个方法）。 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class DailyReportServiceTest {

    @Autowired
    private DailyReportService svc;
    @Autowired
    private DailyReportRepository reportRepo;
    @Autowired
    private UserPreferenceRepository prefRepo;

    private static String today() {
        return LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE);
    }

    @Test
    void getToday_无日报返回空摘要() {
        DailyReportTodayResponse r = svc.getToday("u-dr-empty");
        assertEquals(today(), r.date());
        assertEquals(0, r.stats().appliedTotal());
        assertEquals(0, r.stats().success());
        assertEquals(0, r.stats().failed());
        assertTrue(r.stats().byPlatform().isEmpty());
        assertTrue(r.stats().trend7d().isEmpty());
        assertNotNull(r.summary());
    }

    @Test
    void getToday_有日报返回统计与趋势() {
        String t = today();
        String y = LocalDate.now().minusDays(1).format(DateTimeFormatter.ISO_LOCAL_DATE);
        // 历史行（昨天）用于 trend7d 派生
        reportRepo.save(new DailyReport("u-dr-1", y, 5, 3, 1, 2, 1, 1,
                "[{\"platformId\":\"p1\",\"count\":5}]"));
        // 今日行
        reportRepo.save(new DailyReport("u-dr-1", t, 10, 6, 2, 4, 2, 3,
                "[{\"platformId\":\"p1\",\"count\":7},{\"platformId\":\"p2\",\"count\":3}]"));

        DailyReportTodayResponse r = svc.getToday("u-dr-1");
        assertEquals(t, r.date());
        assertEquals(10, r.stats().appliedTotal());
        assertEquals(6, r.stats().success());
        assertEquals(2, r.stats().failed());
        assertEquals(4, r.stats().hrViews());
        assertEquals(2, r.stats().interviewInvites());
        assertEquals(3, r.stats().newQuestions());
        assertEquals(2, r.stats().byPlatform().size());
        // trend7d 含今日与前一日，按日期降序，首条为今日
        assertEquals(2, r.stats().trend7d().size());
        assertEquals(t, r.stats().trend7d().get(0).date());
        assertEquals(10, r.stats().trend7d().get(0).count());
    }

    @Test
    void updatePreference_新建并返回updatedAt() {
        DailyReportPreferenceResponse r = svc.updatePreference("u-pref-1", "21:30", true);
        assertTrue(r.ok());
        assertTrue(r.updatedAt() > 0);
        UserPreference up = prefRepo.findById("u-pref-1").orElseThrow();
        assertEquals("21:30", up.getDailyReportPushTime());
        assertTrue(up.isDailyReportEnabled());
    }

    @Test
    void updatePreference_重复更新幂等() {
        svc.updatePreference("u-pref-2", "08:00", true);
        svc.updatePreference("u-pref-2", "22:00", false);
        UserPreference up = prefRepo.findById("u-pref-2").orElseThrow();
        assertEquals("22:00", up.getDailyReportPushTime());
        assertFalse(up.isDailyReportEnabled());
        assertEquals(1, prefRepo.count()); // upsert 幂等，仍为单行
    }

    @Test
    void updatePreference_非法时间抛异常() {
        BizException ex = assertThrows(BizException.class,
                () -> svc.updatePreference("u-pref-3", "99:99", true));
        assertEquals(400, ex.getCode());
    }
}
