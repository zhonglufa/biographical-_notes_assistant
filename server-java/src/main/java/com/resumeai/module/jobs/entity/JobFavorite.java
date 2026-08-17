package com.resumeai.module.jobs.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 岗位收藏 / 忽略 / 软删（job_favorite · A08）。
 * action ∈ {favorite, ignore, removed}；ignore 供状态机模块 §3.4 投递推荐过滤。
 */
@Entity
@Table(name = "job_favorite")
@IdClass(JobFavoriteId.class)
@Getter
@Setter
@NoArgsConstructor
public class JobFavorite {
    @Id
    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Id
    @Column(name = "job_id", nullable = false)
    private Long jobId;

    @Column(nullable = false)
    private String action;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;
}
