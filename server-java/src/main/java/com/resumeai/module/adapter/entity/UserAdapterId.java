package com.resumeai.module.adapter.entity;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;

/** 复合主键（user_id, platform_id）· 用户×适配器启停态。作为 @IdClass 使用。 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class UserAdapterId implements Serializable {
    private String userId;
    private String platformId;
}
