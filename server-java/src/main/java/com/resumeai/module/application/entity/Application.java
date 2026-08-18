package com.resumeai.module.application.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 投递记录实体（对齐 LLD-数据库设计 §2.1 / HLD §3.4）。
 *
 * <p>关键约束（防重投命门，必须忠实）：
 * <ul>
 *   <li>{@code idempotency_key}（请求级幂等 A09 前端 UUID）—— <b>审计列，非唯一</b>。
 *       一个批量投递请求（applyBatch）会为 N 个岗位生成 N 行 application，它们共享同一个
 *       {@code idempotency_key}，因此该列<b>不能</b>做行级唯一；请求级幂等由
 *       {@code IdempotencyStore}（生产 Redis SETNX，返回 409）强制，数据库列仅作审计溯源。</li>
 *   <li>{@code uk(user_id, platform_id, job_id, apply_date)} —— 业务级四元组唯一索引（ADR-006）；
 *       是「同用户同日对同岗不重投」的数据库层强制。</li>
 * </ul>
 *
 * <p>TODO(对齐 LLD §2.1 主键形态): 生产应改为 {@code (user_id, id)} 复合主键 {@code @IdClass}。
 * P0 简化单列 UUID {@code id} + {@code user_id} 列，仍满足四元组唯一约束与数据隔离语义。</p>
 */
@Entity
@Table(name = "application",
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_application_biz",
                        columnNames = {"user_id", "platform_id", "job_id", "apply_date"})
        },
        indexes = { @Index(name = "idx_application_user", columnList = "user_id") }
)
@Getter
@Setter
@NoArgsConstructor
public class Application {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Column(name = "job_id", nullable = false)
    private String jobId;

    @Column(name = "platform_id", nullable = false)
    private String platformId;

    @Column(name = "status", nullable = false, length = 20)
    private String status;

    @Column(name = "resume_version_id")
    private String resumeVersionId;

    @Column(name = "idempotency_key", length = 64)
    private String idempotencyKey;

    /** 业务级幂等四元组之一：投递日期 yyyy-MM-dd（按用户本地日期）。 */
    @Column(name = "apply_date", nullable = false, length = 10)
    private String applyDate;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;

    @Column(name = "updated_at", nullable = false)
    private Long updatedAt;
}
