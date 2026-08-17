package com.resumeai.module.resume.repository;

import com.resumeai.module.resume.entity.AtsReport;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/** ATS 评分报告仓储（ats_report）。 */
@Repository
public interface AtsReportRepository extends JpaRepository<AtsReport, Long> {
}
