package com.resumeai.module.interview.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 面试评估报告（对齐 DB interview_evaluation，G7-2 透明可申诉）。
 * dimensions 存 JSON 字符串（逐维度原始分+理由+归一化分）。
 */
@TableName("interview_evaluation")
@Getter
@Setter
@NoArgsConstructor
public class InterviewEvaluation {
    @TableId(type = IdType.INPUT)
    private Long sessionId;

    @TableField("weighted_score")
    private int weightedScore;

    @TableField("dimensions")
    private String dimensions;

    @TableField("degrade_flag")
    private boolean degradeFlag= false;

    @TableField("appeal_entry")
    private boolean appealEntry= false;

    @TableField("rerun_entry")
    private boolean rerunEntry= false;

    @TableField("created_at")
    private Long createdAt= System.currentTimeMillis();
}
