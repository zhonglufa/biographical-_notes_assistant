package com.resumeai.module.application;

/**
 * 投递任务下发器（对齐 HLD §3.4.1 C2 任务通道 / B06）。
 * <p>经任务通道下发至用户本机 Agent（载荷<b>不含 Cookie</b>，Cookie 由本机 Agent 本地加载）。</p>
 * <p>TODO(P0→生产): 当前由 {@link InMemoryApplyTaskPublisher} 内存实现；
 * 生产须替换为 RabbitMQ（direct + topic + DLQ，ADR-004），并加设备级鉴权。</p>
 */
public interface ApplyTaskPublisher {

    /**
     * 下发一次投递任务，返回 taskId（与 application_task 主键一致）。
     */
    String publish(String applicationId, String platformId, String jobId,
                   String idempotencyKey, String resumeVersionId);
}
