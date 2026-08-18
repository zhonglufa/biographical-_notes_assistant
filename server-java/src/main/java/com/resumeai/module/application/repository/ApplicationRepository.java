package com.resumeai.module.application.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.application.entity.Application;
import org.springframework.stereotype.Repository;


/**
 * 投递记录仓储（对齐 LLD-数据库设计 §2.1）。
 * 数据隔离：所有查询以 {@code userId} 为前缀，防越权读他人数据（A11 403 FORBIDDEN 由 service 兜底）。
 */
@Repository
public interface ApplicationRepository extends BaseMapper<Application> {





    default Optional<Application> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default Application save(Application e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<Application> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default List<Application> findByUserIdOrderByUpdatedAtDesc(String userId) {
        return selectList(new QueryWrapper<Application>().eq("user_id", userId).orderByDesc("updated_at"));
    }

    default long countByUserId(String userId) {
        return selectCount(new QueryWrapper<Application>().eq("user_id", userId));
    }

    default Optional<Application> findByUserIdAndId(String userId, String id) {
        return Optional.ofNullable(selectOne(new QueryWrapper<Application>().eq("user_id", userId).eq("id", id)));
    }

    default boolean existsByUserIdAndPlatformIdAndJobIdAndApplyDate(String userId, String platformId, String jobId, String applyDate) {
        return selectCount(new QueryWrapper<Application>().eq("user_id", userId).eq("platform_id", platformId).eq("job_id", jobId).eq("apply_date", applyDate)) > 0;
    }

}
