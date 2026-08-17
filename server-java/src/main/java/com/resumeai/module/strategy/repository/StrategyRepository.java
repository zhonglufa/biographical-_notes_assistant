package com.resumeai.module.strategy.repository;

import com.resumeai.module.strategy.entity.StrategyConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * 策略配置仓储（对齐 LLD-策略配置模块 §5）。
 * 每用户一行：以 {@code userId} 为主键，{@code findByUserId} 即 upsert 读端。
 */
@Repository
public interface StrategyRepository extends JpaRepository<StrategyConfig, String> {

    Optional<StrategyConfig> findByUserId(String userId);
}
