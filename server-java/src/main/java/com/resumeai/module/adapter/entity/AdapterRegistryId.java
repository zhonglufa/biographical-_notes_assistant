package com.resumeai.module.adapter.entity;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;

/** 复合主键（platform_id, version）· 对齐 LLD-数据库设计 adapter_registry。作为 @IdClass 使用。 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class AdapterRegistryId implements Serializable {
    private String platformId;
    private String version;
}
