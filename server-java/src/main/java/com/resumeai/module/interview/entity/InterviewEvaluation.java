package com.resumeai.module.interview.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 面试评估报告（对齐 DB interview_evaluation，G7-2 透明可申诉）。
 * dimensions 存 JSON 字符串（逐维度原始分+理由+归一化分）。
 */
@Entity
@Table(name = "interview_evaluation")
@Getter
@Setter
@NoArgsConstructor
public class InterviewEvaluation {
    @Id
    @Column(name = "session_id")
    private Long sessionId;

    @Column(name = "weighted_score", nullable = false)
    private int weightedScore;

    @Lob
    @Column(nullable = false, columnDefinition = "TEXT")
    private String dimensions;

    @Column(name = "degrade_flag", nullable = false)
    private boolean degradeFlag = false;

    @Column(name = "appeal_entry")
    private boolean appealEntry = false;

    @Column(name = "rerun_entry")
    private boolean rerunEntry = false;

    @Column(name = "created_at")
    private Long createdAt = System.currentTimeMillis();
}
