package com.resumeai.module.resume.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.resume.entity.Resume;
import org.springframework.stereotype.Repository;


/** 简历头部仓储（resume）。 */
@Repository
public interface ResumeRepository extends BaseMapper<Resume> {


    default Optional<Resume> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default Resume save(Resume e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<Resume> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default Optional<Resume> findByUserIdAndId(String userId, Long id) {
        return Optional.ofNullable(selectOne(new QueryWrapper<Resume>().eq("user_id", userId).eq("id", id)));
    }

}
