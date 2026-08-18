package com.resumeai.module.jobs.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 用户×岗位匹配度反范式缓存（job_match · A07 列表 O(1)/行读取）。
 * 由异步匹配管道（B01）填充；列表缺失返回 null。
 */
@TableName("job_match")
@Getter
@Setter
@NoArgsConstructor
public class JobMatch {
    @TableId(type = IdType.INPUT)
    private String userId;

    // 复合主键第二列：MBP 不支持多 @TableId，降级为普通字段（仍由 Flyway 建复合 PK）。
    @TableField("job_id")
    private Long jobId;

    @TableField("resume_version_id")
    private Long resumeVersionId;

    @TableField("score")
    private Integer score;

    // 注意：band 是 OGNL 保留字（按位与运算符），MBP 自动生成的 <if test="band != null"> 会因 OGNL 解析失败而炸。
    // 故用 insertStrategy/updateStrategy = ALWAYS，让 MBP 无条件包含该列、不生成 band 相关的动态 <if>。
    @TableField(value = "band", insertStrategy = FieldStrategy.ALWAYS, updateStrategy = FieldStrategy.ALWAYS)
    private String band; // green | blue | gray

    @TableField("reason")
    private String reason;

    @TableField("computed_at")
    private Long computedAt;
}
