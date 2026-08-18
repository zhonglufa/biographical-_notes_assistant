package com.resumeai.module.resume.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.resume.entity.AtsReport;
import org.springframework.stereotype.Repository;

/** ATS 评分报告仓储（ats_report）。 */
@Repository
public interface AtsReportRepository extends BaseMapper<AtsReport> {

    default Optional<AtsReport> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default AtsReport save(AtsReport e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<AtsReport> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
}
