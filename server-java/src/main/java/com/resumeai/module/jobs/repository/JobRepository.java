package com.resumeai.module.jobs.repository;

import com.resumeai.module.jobs.entity.Job;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

/**
 * 岗位读模型仓储（只读 · 不抓取）。
 * 动态过滤：keyword/location/platform/salaryMin 为 null 时忽略该条件；默认按 collected_at DESC。
 */
@Repository
public interface JobRepository extends JpaRepository<Job, Long> {

    @Query("SELECT j FROM Job j " +
           "WHERE (:keyword IS NULL OR j.title LIKE %:keyword%) " +
           "AND (:location IS NULL OR j.location = :location) " +
           "AND (:platform IS NULL OR j.platformId = :platform) " +
           "AND (:salaryMin IS NULL OR j.salaryMin >= :salaryMin) " +
           "ORDER BY j.collectedAt DESC")
    Page<Job> search(@Param("keyword") String keyword,
                     @Param("location") String location,
                     @Param("platform") String platform,
                     @Param("salaryMin") Integer salaryMin,
                     Pageable pageable);
}
