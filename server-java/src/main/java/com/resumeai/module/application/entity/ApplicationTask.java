package com.resumeai.module.application.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 投递执行单元（对齐 LLD §5 / HLD §3.4 孤儿清扫 R2）。
 * 由服务端经 C2 任务通道下发本机 Agent；结果经 C3 回写。本机 Agent 不持业务库。
 *
 * <p>status: pending/running/done/failed；outcome: success/failed/captcha/risk_blocked/need_login
 * （与 B06 结果事件对齐）。{@code idempotency_key} 与 application 同属一个批量请求，N 个任务共享同一
 * key，故为<b>审计列、非唯一</b>；任务级重复下发由 {@code IdempotencyStore}（生产 Redis SETNX）兜底。</p>
 */
@TableName("application_task")
@Getter
@Setter
@NoArgsConstructor
public class ApplicationTask {

    @TableId(type = IdType.INPUT)
    private String id;

    @TableField("user_id")
    private String userId;

    @TableField("application_id")
    private String applicationId;

    @TableField("idempotency_key")
    private String idempotencyKey;

    @TableField("platform_id")
    private String platformId;

    @TableField("job_id")
    private String jobId;

    @TableField("status")
    private String status;

    @TableField("outcome")
    private String outcome;

    @TableField("platform_apply_id")
    private String platformApplyId;

    @TableField("fail_reason")
    private String failReason;

    @TableField("evidence")
    private String evidence;

    @TableField("created_at")
    private Long createdAt;

    @TableField("updated_at")
    private Long updatedAt;
}
