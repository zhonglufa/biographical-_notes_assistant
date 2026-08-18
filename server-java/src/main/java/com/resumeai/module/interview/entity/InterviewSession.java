package com.resumeai.module.interview.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 面试会话（对齐 DB interview_session）。
 * 状态机：created→active→in_progress⇄paused→completed→scored→archived，abandoned 终态（LLD G7-1）。
 * 注意：DB 设计为 (user_id,id) 复合主键；Java 实体用单 @Id 简化（H2 测试稳定），Flyway 生产 DDL 用复合主键。
 */
@Entity
@Table(name = "interview_session")
@Getter
@Setter
@NoArgsConstructor
public class InterviewSession {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String userId;

    @Column(name = "question_set_id")
    private Long questionSetId;

    @Column(name = "application_id")
    private Long applicationId;

    @Column(nullable = false)
    private String state = "created";

    @Column(nullable = false)
    private String mode = "text";

    @Column(name = "current_turn")
    private Integer currentTurn = 0;

    @Column(name = "started_at")
    private Long startedAt;

    @Column(name = "ended_at")
    private Long endedAt;

    @Column(name = "created_at")
    private Long createdAt = System.currentTimeMillis();
}
