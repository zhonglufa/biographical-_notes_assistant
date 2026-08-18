package com.resumeai.module.dailyreport.repository;

import com.resumeai.module.dailyreport.entity.DailyReport;
import com.resumeai.module.dailyreport.entity.DailyReportId;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface DailyReportRepository extends JpaRepository<DailyReport, DailyReportId> {
    Optional<DailyReport> findByUserIdAndReportDate(String userId, String reportDate);

    /** 最近 N 天日报（按日期降序），供 trend7d 派生（LLD §1）。 */
    List<DailyReport> findByUserIdOrderByReportDateDesc(String userId, Pageable pageable);
}
