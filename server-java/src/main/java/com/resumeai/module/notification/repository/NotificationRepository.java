package com.resumeai.module.notification.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.notification.entity.Notification;

public interface NotificationRepository extends BaseMapper<Notification> {



    default Optional<Notification> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default Notification save(Notification e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<Notification> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default List<Notification> findByUserIdOrderByCreatedAtDesc(String userId) {
        return selectList(new QueryWrapper<Notification>().eq("user_id", userId).orderByDesc("created_at"));
    }

    default int countByUserIdAndReadFlagFalse(String userId) {
        return (int) selectCount(new QueryWrapper<Notification>().eq("user_id", userId).eq("read_flag", false));
    }

}
