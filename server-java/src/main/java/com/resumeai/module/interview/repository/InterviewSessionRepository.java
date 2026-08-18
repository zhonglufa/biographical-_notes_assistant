package com.resumeai.module.interview.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.interview.entity.InterviewSession;

public interface InterviewSessionRepository extends BaseMapper<InterviewSession> {


    default Optional<InterviewSession> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default InterviewSession save(InterviewSession e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<InterviewSession> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default Optional<InterviewSession> findByUserIdAndId(String userId, Long id) {
        return Optional.ofNullable(selectOne(new QueryWrapper<InterviewSession>().eq("user_id", userId).eq("id", id)));
    }

}
