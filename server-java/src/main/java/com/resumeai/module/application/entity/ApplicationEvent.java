package com.resumeai.module.application.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 投递状态变更审计事件（溯源 · 对齐 LLD §5 / ADR-008）。
 * 每状态转移写一条，供时间线展示与「apply.status.changed」广播（通知/AI/推荐监听）。
 */
@TableName("application_event")
@Getter
@Setter
@NoArgsConstructor
public class ApplicationEvent {

    @TableId(type = IdType.INPUT)
    private String id;

    @TableField("user_id")
    private String userId;

    @TableField("application_id")
    private String applicationId;

    @TableField("from_state")
    private String fromState;

    @TableField("to_state")
    private String toState;

    @TableField("reason")
    private String reason;

    @TableField("occurred_at")
    private Long occurredAt;
}
