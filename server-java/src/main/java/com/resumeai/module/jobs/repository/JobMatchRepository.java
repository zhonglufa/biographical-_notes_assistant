package com.resumeai.module.jobs.repository;

import com.resumeai.module.jobs.entity.JobMatch;
import com.resumeai.module.jobs.entity.JobMatchId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/** 匹配度缓存仓储（job_match）。 */
@Repository
public interface JobMatchRepository extends JpaRepository<JobMatch, JobMatchId> {
    Optional<JobMatch> findByUserIdAndJobId(String userId, Long jobId);
}
