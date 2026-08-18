package com.resumeai.module.resume.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.resume.entity.ResumeVersion;
import org.springframework.stereotype.Repository;


/** 简历版本快照仓储（resume_version）。 */
@Repository
public interface ResumeVersionRepository extends BaseMapper<ResumeVersion> {




    default Optional<ResumeVersion> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default ResumeVersion save(ResumeVersion e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<ResumeVersion> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default List<ResumeVersion> findByResumeIdOrderByVersionNoAsc(Long resumeId) {
        return selectList(new QueryWrapper<ResumeVersion>().eq("resume_id", resumeId).orderByAsc("version_no"));
    }

    default Optional<ResumeVersion> findByResumeIdAndId(Long resumeId, Long id) {
        return Optional.ofNullable(selectOne(new QueryWrapper<ResumeVersion>().eq("resume_id", resumeId).eq("id", id)));
    }

    default Optional<ResumeVersion> findByUserIdAndId(String userId, Long id) {
        return Optional.ofNullable(selectOne(new QueryWrapper<ResumeVersion>().eq("user_id", userId).eq("id", id)));
    }

}
