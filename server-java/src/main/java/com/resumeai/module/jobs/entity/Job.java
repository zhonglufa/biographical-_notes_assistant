package com.resumeai.module.jobs.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 岗位读模型（映射采集入库的 {@code job} 表 · 对齐 LLD-数据库设计 §3.1）。
 * 本模块对岗位只读（不抓取；B10/B11 由 Python 采集器经 Alembic 入库）。
 * API 暴露的 {@code jobId} = 内部 {@code id} 的字符串形式（TODO：A26/A27 细节端明确外部 id 语义）。
 */
@Entity
@Table(name = "job")
@Getter
@Setter
@NoArgsConstructor
public class Job {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "platform_id", length = 32, nullable = false)
    private String platformId;

    @Column(name = "external_id", length = 128)
    private String externalId;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false)
    private String company;

    @Column(length = 1024)
    private String url;

    @Column(name = "salary_min")
    private Integer salaryMin;

    @Column(name = "salary_max")
    private Integer salaryMax;

    @Column(length = 128)
    private String location;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "jd_raw", columnDefinition = "JSON")
    private String jdRaw;

    @Column(nullable = false)
    private String source; // 'search' | 'detail'

    @Column(name = "collected_at", nullable = false)
    private Long collectedAt;
}
