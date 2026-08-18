package com.resumeai.module.application.entity;
import com.baomidou.mybatisplus.annotation.*;

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
 * <p>主键形态（对齐 LLD §2.1）：采用单列 UUID {@code id}（{@code @TableId(INPUT)}）+ {@code user_id} 列，
 * 配合业务级四元组唯一索引 uk(user_id, platform_id, job_id, apply_date)（ADR-006）实现「同用户同日对同岗不重投」，
 * 同时满足数据隔离语义（service 层按 userId 前缀查询）。早期 JPA 时代设想的复合 {@code @IdClass} 方案已废弃。</p>
 */
@TableName("application")
@Getter
@Setter
@NoArgsConstructor
public class Application {

    @TableId(type = IdType.INPUT)
    private String id;

    @TableField("user_id")
    private String userId;

    @TableField("job_id")
    private String jobId;

    @TableField("platform_id")
    private String platformId;

    @TableField("status")
    private String status;

    @TableField("resume_version_id")
    private String resumeVersionId;

    @TableField("idempotency_key")
    private String idempotencyKey;

    /** 业务级幂等四元组之一：投递日期 yyyy-MM-dd（按用户本地日期）。 */
    @TableField("apply_date")
    private String applyDate;

    @TableField("created_at")
    private Long createdAt;

    @TableField("updated_at")
    private Long updatedAt;
}
