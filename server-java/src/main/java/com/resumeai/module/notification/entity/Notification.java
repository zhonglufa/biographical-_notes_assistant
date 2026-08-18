package com.resumeai.module.notification.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 通知（站内信，对齐 DB notification，LLD §7 状态机 sent→read/deleted，到期 archived）。
 * userId 沿用 P0/P1 的 String(36) 约定（与 LLD BIGINT 偏差已登记）。
 */
@TableName("notification")
@Getter
@Setter
@NoArgsConstructor
public class Notification {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private String userId;

    @TableField("channel")
    private String channel; // push/inbox/email/sms

    @TableField("level")
    private String level; // L0-L3

    @TableField("title")
    private String title;

    @TableField("body")
    private String body;

    @TableField("read_flag")
    private boolean readFlag= false;

    @TableField("sent_at")
    private Long sentAt;

    @TableField("created_at")
    private Long createdAt= System.currentTimeMillis();

    @TableField("notification_key")
    private String notificationKey; // 去重键（LLD §8 at-least-once + 幂等）
}
