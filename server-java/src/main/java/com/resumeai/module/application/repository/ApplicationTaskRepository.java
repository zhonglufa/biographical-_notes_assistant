package com.resumeai.module.application.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.application.entity.ApplicationTask;
import org.springframework.stereotype.Repository;


@Repository
public interface ApplicationTaskRepository extends BaseMapper<ApplicationTask> {


    default Optional<ApplicationTask> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default ApplicationTask save(ApplicationTask e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<ApplicationTask> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default Optional<ApplicationTask> findByApplicationId(String applicationId) {
        return Optional.ofNullable(selectOne(new QueryWrapper<ApplicationTask>().eq("application_id", applicationId)));
    }

}
