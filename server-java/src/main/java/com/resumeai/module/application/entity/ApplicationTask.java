package com.resumeai.module.application.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 投递执行单元（对齐 LLD §5 / HLD §3.4 孤儿清扫 R2）。
 * 由服务端经 C2 任务通道下发本机 Agent；结果经 C3 回写。本机 Agent 不持业务库。
 *
 * <p>status: pending/running/done/failed；outcome: success/failed/captcha/risk_blocked/need_login
 * （与 B06 结果事件对齐）。{@code uk(idempotency_key)} 防任务重复下发。</p>
 */
@Entity
@Table(name = "application_task",
        uniqueConstraints = { @UniqueConstraint(name = "uk_task_idem", columnNames = "idempotency_key") },
        indexes = { @Index(name = "idx_task_application", columnList = "application_id") }
)
@Getter
@Setter
@NoArgsConstructor
public class ApplicationTask {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Column(name = "application_id", nullable = false, length = 36)
    private String applicationId;

    @Column(name = "idempotency_key", length = 64)
    private String idempotencyKey;

    @Column(name = "platform_id")
    private String platformId;

    @Column(name = "job_id")
    private String jobId;

    @Column(name = "status", length = 20)
    private String status;

    @Column(name = "outcome", length = 20)
    private String outcome;

    @Column(name = "platform_apply_id")
    private String platformApplyId;

    @Column(name = "fail_reason")
    private String failReason;

    @Column(name = "evidence")
    private String evidence;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;

    @Column(name = "updated_at", nullable = false)
    private Long updatedAt;
}
