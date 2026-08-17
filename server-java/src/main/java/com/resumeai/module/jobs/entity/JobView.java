package com.resumeai.module.jobs.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 岗位浏览记录（job_view · §3.3 离线缓存辅助 / 最近浏览）。
 * 生产按 (user_id, viewed_at) 月度分区；本骨架以 id 自增为主键（TODO：与 DB LLD 复合主键对齐）。
 */
@Entity
@Table(name = "job_view")
@Getter
@Setter
@NoArgsConstructor
public class JobView {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Column(name = "job_id", nullable = false)
    private Long jobId;

    @Column(name = "viewed_at", nullable = false)
    private Long viewedAt;

    @Column(length = 32)
    private String source;
}
