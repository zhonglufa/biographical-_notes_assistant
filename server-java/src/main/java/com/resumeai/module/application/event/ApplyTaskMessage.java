package com.resumeai.module.application.event;

/**
 * 投递任务下发消息体（对齐 ADR-004：消息体只放业务最小必要字段）。
 * <p>载荷不含 Cookie；Cookie 由本机 Agent 本地加载（对齐 HLD §3.4.1 C2 任务通道）。
 * 每条消息必须携带 trace_id 以串联全链路日志（ADR-004）。</p>
 *
 * @param taskId          与 application_task 主键一致（发布侧生成）
 * @param applicationId   投递记录 ID
 * @param platformId      目标平台 ID（P0 占位 "pending"，待 job 模块解析）
 * @param jobId           岗位 ID
 * @param idempotencyKey  请求级幂等键（消费者 Redis 去重依据之一）
 * @param resumeVersionId 简历版本 ID
 * @param traceId         全链路追踪 ID
 */
public record ApplyTaskMessage(
        String taskId,
        String applicationId,
        String platformId,
        String jobId,
        String idempotencyKey,
        String resumeVersionId,
        String traceId) {
}
