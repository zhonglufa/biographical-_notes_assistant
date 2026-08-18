package com.resumeai.module.application.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.application.entity.ApplicationEvent;
import org.springframework.stereotype.Repository;


@Repository
public interface ApplicationEventRepository extends BaseMapper<ApplicationEvent> {


    default Optional<ApplicationEvent> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default ApplicationEvent save(ApplicationEvent e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<ApplicationEvent> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default List<ApplicationEvent> findByApplicationIdOrderByOccurredAtAsc(String applicationId) {
        return selectList(new QueryWrapper<ApplicationEvent>().eq("application_id", applicationId).orderByAsc("occurred_at"));
    }

}
