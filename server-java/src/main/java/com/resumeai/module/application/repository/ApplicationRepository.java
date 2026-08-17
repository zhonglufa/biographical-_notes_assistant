package com.resumeai.module.application.repository;

import com.resumeai.module.application.entity.Application;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 投递记录仓储（对齐 LLD-数据库设计 §2.1）。
 * 数据隔离：所有查询以 {@code userId} 为前缀，防越权读他人数据（A11 403 FORBIDDEN 由 service 兜底）。
 */
@Repository
public interface ApplicationRepository extends JpaRepository<Application, String> {

    List<Application> findByUserIdOrderByUpdatedAtDesc(String userId);

    long countByUserId(String userId);

    Optional<Application> findByUserIdAndId(String userId, String id);

    boolean existsByUserIdAndPlatformIdAndJobIdAndApplyDate(
            String userId, String platformId, String jobId, String applyDate);
}
