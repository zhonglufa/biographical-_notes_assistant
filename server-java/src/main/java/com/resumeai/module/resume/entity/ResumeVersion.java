package com.resumeai.module.resume.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 简历版本快照（resume_version · 快照式版本管理 ADR-012）。
 * snapshot 为解析后结构化简历 JSON（AES-256-GCM，is_encrypted）；raw_file_ref 为 OSS 外链不落库。
 * PK 用 id 自增（DB LLD 为 (user_id, id)，已登记与 JPA 简化实现偏差）。
 */
@TableName("resume_version")
@Getter
@Setter
@NoArgsConstructor
public class ResumeVersion {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("resume_id")
    private Long resumeId;

    @TableField("user_id")
    private String userId;

    @TableField("version_no")
    private int versionNo;

    @TableField("snapshot")
    private String snapshot;

    @TableField("raw_file_ref")
    private String rawFileRef;

    @TableField("is_encrypted")
    private boolean encrypted= true;

    @TableField("created_at")
    private Long createdAt;
}
