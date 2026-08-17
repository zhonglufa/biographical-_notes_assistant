package com.resumeai.module.jobs.repository;

import com.resumeai.module.jobs.entity.JobFavorite;
import com.resumeai.module.jobs.entity.JobFavoriteId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/** 收藏 / 忽略仓储（job_favorite）。 */
@Repository
public interface JobFavoriteRepository extends JpaRepository<JobFavorite, JobFavoriteId> {
    Optional<JobFavorite> findByUserIdAndJobId(String userId, Long jobId);
}
