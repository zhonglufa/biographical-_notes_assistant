package com.resumeai.module.jobs.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.jobs.entity.JobView;
import org.springframework.stereotype.Repository;

/** 浏览记录仓储（job_view）。 */
@Repository
public interface JobViewRepository extends BaseMapper<JobView> {

    default Optional<JobView> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default JobView save(JobView e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<JobView> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
}
