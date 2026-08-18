package com.resumeai.module.dailyreport.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.dailyreport.entity.DailyReport;
import org.springframework.data.domain.Pageable;

public interface DailyReportRepository extends BaseMapper<DailyReport> {


    /** 最近 N 天日报（按日期降序），供 trend7d 派生（LLD §1）。 */


    default DailyReport save(DailyReport e) { insert(e); return e; }
    default Optional<DailyReport> findByUserIdAndReportDate(String userId, String reportDate) {
        return Optional.ofNullable(selectOne(new QueryWrapper<DailyReport>().eq("user_id", userId).eq("report_date", reportDate)));
    }

    default List<DailyReport> findByUserIdOrderByReportDateDesc(String userId, Pageable pageable) {
        Page<DailyReport> page = new Page<>(pageable.getPageNumber() + 1, pageable.getPageSize());
        page = selectPage(page, new QueryWrapper<DailyReport>().eq("user_id", userId).orderByDesc("report_date"));
        return page.getRecords();
    }

}
