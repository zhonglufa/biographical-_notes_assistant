package com.resumeai.module.interview.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 面试会话事件审计（对齐 DB interview_session_event，G7-1 硬要求：每态变更必写）。
 */
@TableName("interview_session_event")
@Getter
@Setter
@NoArgsConstructor
public class InterviewSessionEvent {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private String userId;

    @TableField("session_id")
    private Long sessionId;

    @TableField("from_state")
    private String fromState;

    @TableField("to_state")
    private String toState;

    @TableField("reason")
    private String reason;

    @TableField("actor")
    private String actor= "system";

    @TableField("created_at")
    private Long createdAt= System.currentTimeMillis();
}
