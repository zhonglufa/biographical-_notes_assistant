package com.resumeai.module.adapter.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 用户 × 适配器启停态（user_adapter · A15 编排）。
 * 仅记录用户侧开关；平台执行在本机 Agent，服务端不直连平台、不持 Cookie（HLD §3.6 红线）。
 */
@TableName("user_adapter")
@Getter
@Setter
@NoArgsConstructor
public class UserAdapter {
    @TableId(type = IdType.INPUT)
    private String userId;

    @TableId(type = IdType.INPUT)
    private String platformId;

    @TableField("enabled")
    private boolean enabled;

    @TableField("created_at")
    private Long createdAt;
}
