package com.resumeai.module.notification.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 通知（站内信，对齐 DB notification，LLD §7 状态机 sent→read/deleted，到期 archived）。
 * userId 沿用 P0/P1 的 String(36) 约定（与 LLD BIGINT 偏差已登记）。
 */
@Entity
@Table(name = "notification")
@Getter
@Setter
@NoArgsConstructor
public class Notification {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String userId;

    @Column(nullable = false)
    private String channel; // push/inbox/email/sms

    @Column(nullable = false)
    private String level; // L0-L3

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String body;

    @Column(name = "read_flag", nullable = false)
    private boolean readFlag = false;

    @Column(name = "sent_at")
    private Long sentAt;

    @Column(name = "created_at")
    private Long createdAt = System.currentTimeMillis();

    @Column(name = "notification_key", unique = true)
    private String notificationKey; // 去重键（LLD §8 at-least-once + 幂等）
}
