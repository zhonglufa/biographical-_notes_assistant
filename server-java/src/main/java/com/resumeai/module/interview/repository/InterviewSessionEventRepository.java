package com.resumeai.module.interview.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.interview.entity.InterviewSessionEvent;
public interface InterviewSessionEventRepository extends BaseMapper<InterviewSessionEvent> {

    default Optional<InterviewSessionEvent> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default InterviewSessionEvent save(InterviewSessionEvent e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<InterviewSessionEvent> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
}
