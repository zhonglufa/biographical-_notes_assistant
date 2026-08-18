package com.resumeai.module.adapter.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 平台适配器包元数据（adapter_registry · 全局，非 per-user）。
 * 由部署清单/配置中心注册（TODO：明确填充机制）；status ∈ active|deprecated|disabled。
 */
@TableName("adapter_registry")
@Getter
@Setter
@NoArgsConstructor
public class AdapterRegistry {
    @TableId(type = IdType.INPUT)
    private String platformId;

    @TableId(type = IdType.INPUT)
    private String version;

    @TableField("status")
    private String status; // active | deprecated | disabled

    @TableField("checksum")
    private String checksum;

    @TableField("signature")
    private String signature;

    @TableField("created_at")
    private Long createdAt;
}
