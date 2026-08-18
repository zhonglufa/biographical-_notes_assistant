package com.resumeai.module.strategy.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.strategy.entity.StrategyConfig;
import org.springframework.stereotype.Repository;


/**
 * 策略配置仓储（对齐 LLD-策略配置模块 §5）。
 * 每用户一行：以 {@code userId} 为主键，{@code findByUserId} 即 upsert 读端。
 */
@Repository
public interface StrategyRepository extends BaseMapper<StrategyConfig> {


    default Optional<StrategyConfig> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default StrategyConfig save(StrategyConfig e) { if (e.getId() == null) insert(e); else updateById(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<StrategyConfig> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default Optional<StrategyConfig> findByUserId(String userId) {
        return Optional.ofNullable(selectOne(new QueryWrapper<StrategyConfig>().eq("user_id", userId)));
    }

}
