package com.resumeai.module.adapter.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 平台适配器包元数据（adapter_registry · 全局，非 per-user）。
 * 由部署清单/配置中心注册（TODO：明确填充机制）；status ∈ active|deprecated|disabled。
 */
@Entity
@Table(name = "adapter_registry")
@IdClass(AdapterRegistryId.class)
@Getter
@Setter
@NoArgsConstructor
public class AdapterRegistry {
    @Id
    @Column(name = "platform_id", length = 32, nullable = false)
    private String platformId;

    @Id
    @Column(name = "version", length = 32, nullable = false)
    private String version;

    @Column(nullable = false)
    private String status; // active | deprecated | disabled

    @Column(length = 128)
    private String checksum;

    @Column(length = 256)
    private String signature;

    @Column(name = "created_at", nullable = false)
    private Long createdAt;
}
