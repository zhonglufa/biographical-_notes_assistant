package com.resumeai.module.jobs.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 岗位收藏 / 忽略 / 软删（job_favorite · A08）。
 * action ∈ {favorite, ignore, removed}；ignore 供状态机模块 §3.4 投递推荐过滤。
 */
@TableName("job_favorite")
@Getter
@Setter
@NoArgsConstructor
public class JobFavorite {
    @TableId(type = IdType.INPUT)
    private String userId;

    // 复合主键第二列：MBP 不支持多 @TableId，降级为普通字段（仍由 Flyway 建复合 PK）。
    @TableField("job_id")
    private Long jobId;

    @TableField("action")
    private String action;

    @TableField("created_at")
    private Long createdAt;
}
