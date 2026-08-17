package com.resumeai.module.jobs.repository;

import com.resumeai.module.jobs.entity.JobView;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/** 浏览记录仓储（job_view）。 */
@Repository
public interface JobViewRepository extends JpaRepository<JobView, Long> {
}
