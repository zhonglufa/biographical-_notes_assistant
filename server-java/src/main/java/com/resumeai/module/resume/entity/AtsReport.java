package com.resumeai.module.resume.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * ATS 评分报告（ats_report · A06 触发 B05 后回填）。
 * resume_version_id 主键（一份版本一份报告，不每次重算）。
 */
@Entity
@Table(name = "ats_report")
@Getter
@Setter
@NoArgsConstructor
public class AtsReport {
    @Id
    @Column(name = "resume_version_id", nullable = false)
    private Long resumeVersionId;

    @Column(name = "ats_score", nullable = false)
    private int atsScore;

    @Column(columnDefinition = "JSON", nullable = false)
    private String suggestions;

    @Column(nullable = false)
    private String model;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;
}
