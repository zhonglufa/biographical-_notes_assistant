package com.resumeai.module.jobs.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 用户×岗位匹配度反范式缓存（job_match · A07 列表 O(1)/行读取）。
 * 由异步匹配管道（B01）填充；列表缺失返回 null。
 */
@Entity
@Table(name = "job_match")
@IdClass(JobMatchId.class)
@Getter
@Setter
@NoArgsConstructor
public class JobMatch {
    @Id
    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Id
    @Column(name = "job_id", nullable = false)
    private Long jobId;

    @Column(name = "resume_version_id")
    private Long resumeVersionId;

    @Column(nullable = false)
    private Integer score;

    @Column(nullable = false)
    private String band; // green | blue | gray

    @Column(length = 512)
    private String reason;

    @Column(name = "computed_at", nullable = false)
    private Long computedAt;
}
