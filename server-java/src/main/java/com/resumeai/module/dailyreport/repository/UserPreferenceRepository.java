package com.resumeai.module.dailyreport.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.dailyreport.entity.UserPreference;
public interface UserPreferenceRepository extends BaseMapper<UserPreference> {

    default Optional<UserPreference> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default UserPreference save(UserPreference e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<UserPreference> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
}
