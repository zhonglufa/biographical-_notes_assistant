package com.resumeai.module.resume.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 简历版本快照（resume_version · 快照式版本管理 ADR-012）。
 * snapshot 为解析后结构化简历 JSON（AES-256-GCM，is_encrypted）；raw_file_ref 为 OSS 外链不落库。
 * PK 用 id 自增（DB LLD 为 (user_id, id)，已登记与 JPA 简化实现偏差）。
 */
@Entity
@Table(name = "resume_version",
        uniqueConstraints = @UniqueConstraint(name = "uk_resume_ver", columnNames = {"resume_id", "version_no"}))
@Getter
@Setter
@NoArgsConstructor
public class ResumeVersion {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "resume_id", nullable = false)
    private Long resumeId;

    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Column(name = "version_no", nullable = false)
    private int versionNo;

    @Column(columnDefinition = "JSON", nullable = false)
    private String snapshot;

    @Column(name = "raw_file_ref", length = 512)
    private String rawFileRef;

    @Column(name = "is_encrypted", nullable = false)
    private boolean encrypted = true;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;
}
