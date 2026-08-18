package com.resumeai.module.interview.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 面试会话（对齐 DB interview_session）。
 * 状态机：created→active→in_progress⇄paused→completed→scored→archived，abandoned 终态（LLD G7-1）。
 * 注意：DB 设计为 (user_id,id) 复合主键；Java 实体用单 @Id 简化（H2 测试稳定），Flyway 生产 DDL 用复合主键。
 */
@TableName("interview_session")
@Getter
@Setter
@NoArgsConstructor
public class InterviewSession {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private String userId;

    @TableField("question_set_id")
    private Long questionSetId;

    @TableField("application_id")
    private Long applicationId;

    @TableField("state")
    private String state= "created";

    @TableField("mode")
    private String mode= "text";

    @TableField("current_turn")
    private Integer currentTurn= 0;

    @TableField("started_at")
    private Long startedAt;

    @TableField("ended_at")
    private Long endedAt;

    @TableField("created_at")
    private Long createdAt= System.currentTimeMillis();
}
