package com.resumeai.module.interview.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 面试会话事件审计（对齐 DB interview_session_event，G7-1 硬要求：每态变更必写）。
 */
@Entity
@Table(name = "interview_session_event")
@Getter
@Setter
@NoArgsConstructor
public class InterviewSessionEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String userId;

    @Column(name = "session_id", nullable = false)
    private Long sessionId;

    @Column(name = "from_state")
    private String fromState;

    @Column(name = "to_state")
    private String toState;

    private String reason;

    private String actor = "system";

    @Column(name = "created_at")
    private Long createdAt = System.currentTimeMillis();
}
