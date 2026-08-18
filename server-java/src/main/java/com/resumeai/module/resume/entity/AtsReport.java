package com.resumeai.module.resume.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * ATS 评分报告（ats_report · A06 触发 B05 后回填）。
 * resume_version_id 主键（一份版本一份报告，不每次重算）。
 */
@TableName("ats_report")
@Getter
@Setter
@NoArgsConstructor
public class AtsReport {
    @TableId(type = IdType.INPUT)
    private Long resumeVersionId;

    @TableField("ats_score")
    private int atsScore;

    @TableField("suggestions")
    private String suggestions;

    @TableField("model")
    private String model;

    @TableField("created_at")
    private Long createdAt;
}
