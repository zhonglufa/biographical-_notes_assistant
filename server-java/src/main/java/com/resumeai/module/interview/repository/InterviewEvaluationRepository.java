package com.resumeai.module.interview.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.interview.entity.InterviewEvaluation;

public interface InterviewEvaluationRepository extends BaseMapper<InterviewEvaluation> {


    default Optional<InterviewEvaluation> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default InterviewEvaluation save(InterviewEvaluation e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<InterviewEvaluation> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default Optional<InterviewEvaluation> findBySessionId(Long sessionId) {
        return Optional.ofNullable(selectOne(new QueryWrapper<InterviewEvaluation>().eq("session_id", sessionId)));
    }

}
