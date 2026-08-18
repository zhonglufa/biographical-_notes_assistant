package com.resumeai.module.jobs.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 岗位浏览记录（job_view · §3.3 离线缓存辅助 / 最近浏览）。
 * 生产按 (user_id, viewed_at) 月度分区；本骨架以 id 自增为主键（TODO：与 DB LLD 复合主键对齐）。
 */
@TableName("job_view")
@Getter
@Setter
@NoArgsConstructor
public class JobView {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private String userId;

    @TableField("job_id")
    private Long jobId;

    @TableField("viewed_at")
    private Long viewedAt;

    @TableField("source")
    private String source;
}
