package com.resumeai.module.jobs.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 岗位读模型（映射采集入库的 {@code job} 表 · 对齐 LLD-数据库设计 §3.1）。
 * 本模块对岗位只读（不抓取；B10/B11 由 Python 采集器经 Alembic 入库）。
 * API 暴露的 {@code jobId} = 内部 {@code id} 的字符串形式（TODO：A26/A27 细节端明确外部 id 语义）。
 */
@TableName("job")
@Getter
@Setter
@NoArgsConstructor
public class Job {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("platform_id")
    private String platformId;

    @TableField("external_id")
    private String externalId;

    @TableField("title")
    private String title;

    @TableField("company")
    private String company;

    @TableField("url")
    private String url;

    @TableField("salary_min")
    private Integer salaryMin;

    @TableField("salary_max")
    private Integer salaryMax;

    @TableField("location")
    private String location;

    @TableField("description")
    private String description;

    @TableField("jd_raw")
    private String jdRaw;

    @TableField("source")
    private String source; // 'search' | 'detail'

    @TableField("collected_at")
    private Long collectedAt;
}
