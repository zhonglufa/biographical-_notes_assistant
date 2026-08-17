package com.resumeai.module.resume.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 简历头部（resume · A04/A05）。
 * 一份简历多个版本；preferred_version_id 指向默认投递版本。
 * user_id 用 VARCHAR(36) 对齐 P0 userId=String 约定（DB LLD 为 BIGINT，已登记偏差）。
 */
@Entity
@Table(name = "resume")
@Getter
@Setter
@NoArgsConstructor
public class Resume {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Column(nullable = false)
    private String title;

    @Column(name = "preferred_version_id")
    private Long preferredVersionId;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;

    @Column(name = "updated_at", nullable = false)
    private Long updatedAt;
}
