package com.resumeai.module.jobs.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.jobs.entity.Job;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

/**
 * 岗位读模型仓储（只读 · 不抓取）。
 * 动态过滤：keyword/location/platform/salaryMin 为 null 时忽略该条件；默认按 collected_at DESC。
 */
@Repository
public interface JobRepository extends BaseMapper<Job> {

    default org.springframework.data.domain.Page<Job> search(String keyword, String location, String platform, Integer salaryMin, org.springframework.data.domain.Pageable pageable) {
        QueryWrapper<Job> q = new QueryWrapper<Job>();
        if (keyword != null && !keyword.isBlank()) q.like("title", keyword);
        if (location != null && !location.isBlank()) q.eq("location", location);
        if (platform != null && !platform.isBlank()) q.eq("platform_id", platform);
        if (salaryMin != null) q.ge("salary_min", salaryMin);
        q.orderByDesc("collected_at");
        com.baomidou.mybatisplus.extension.plugins.pagination.Page<Job> page = new com.baomidou.mybatisplus.extension.plugins.pagination.Page<>(pageable.getPageNumber() + 1, pageable.getPageSize());
        page = selectPage(page, q);
        return new org.springframework.data.domain.PageImpl<>(page.getRecords(), pageable, page.getTotal());
    }

    default Optional<Job> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default Job save(Job e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<Job> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
}
