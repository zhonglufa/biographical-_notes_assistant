package com.resumeai.module.application.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 投递状态变更审计事件（溯源 · 对齐 LLD §5 / ADR-008）。
 * 每状态转移写一条，供时间线展示与「apply.status.changed」广播（通知/AI/推荐监听）。
 */
@Entity
@Table(name = "application_event",
        indexes = { @Index(name = "idx_ae_application", columnList = "application_id") }
)
@Getter
@Setter
@NoArgsConstructor
public class ApplicationEvent {

    @Id
    @Column(name = "id", length = 36, nullable = false)
    private String id;

    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Column(name = "application_id", nullable = false, length = 36)
    private String applicationId;

    @Column(name = "from_state", length = 20)
    private String fromState;

    @Column(name = "to_state", length = 20)
    private String toState;

    @Column(name = "reason")
    private String reason;

    @Column(name = "occurred_at", nullable = false)
    private Long occurredAt;
}
