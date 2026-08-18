package com.resumeai.module.resume.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 简历头部（resume · A04/A05）。
 * 一份简历多个版本；preferred_version_id 指向默认投递版本。
 * user_id 用 VARCHAR(36) 对齐 P0 userId=String 约定（DB LLD 为 BIGINT，已登记偏差）。
 */
@TableName("resume")
@Getter
@Setter
@NoArgsConstructor
public class Resume {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private String userId;

    @TableField("title")
    private String title;

    @TableField("preferred_version_id")
    private Long preferredVersionId;

    @TableField("created_at")
    private Long createdAt;

    @TableField("updated_at")
    private Long updatedAt;
}
