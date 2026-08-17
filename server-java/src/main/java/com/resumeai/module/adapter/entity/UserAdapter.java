package com.resumeai.module.adapter.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 用户 × 适配器启停态（user_adapter · A15 编排）。
 * 仅记录用户侧开关；平台执行在本机 Agent，服务端不直连平台、不持 Cookie（HLD §3.6 红线）。
 */
@Entity
@Table(name = "user_adapter")
@IdClass(UserAdapterId.class)
@Getter
@Setter
@NoArgsConstructor
public class UserAdapter {
    @Id
    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Id
    @Column(name = "platform_id", length = 32, nullable = false)
    private String platformId;

    @Column(nullable = false)
    private boolean enabled;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;
}
