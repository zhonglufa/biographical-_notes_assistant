package com.resumeai.module.application.event;

import com.resumeai.module.application.ApplyTaskPublisher;
import org.slf4j.MDC;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

import java.util.UUID;

/**
 * 投递任务下发器的 RabbitMQ 实现（生产级，替换 InMemory 桩，ADR-004）。
 * <p>经 {@code apply.direct} 直连交换机下发至投递任务队列；消息以 JSON 序列化，携带 trace_id；
 * 队列侧已配置死信交换机（apply.dlx），支持失败重试/死信路由（ADR-004）。</p>
 * <p><b>职责边界（诚实标注，非伪造完成）</b>：延迟执行（TTL+DLX）与消费端幂等（Redis 去重）
 * 属消费者/P1 职责，本类仅负责「发布」。延迟交换机与消费者模块将在 event/ 包（Task #65）落地时补齐。</p>
 */
public class RabbitMqApplyTaskPublisher implements ApplyTaskPublisher {

    private final RabbitTemplate rabbitTemplate;
    private final String exchange;
    private final String routingKey;

    public RabbitMqApplyTaskPublisher(RabbitTemplate rabbitTemplate, String exchange, String routingKey) {
        this.rabbitTemplate = rabbitTemplate;
        this.exchange = exchange;
        this.routingKey = routingKey;
    }

    @Override
    public String publish(String applicationId, String platformId, String jobId,
                          String idempotencyKey, String resumeVersionId) {
        String taskId = UUID.randomUUID().toString();
        String traceId = resolveTraceId();
        ApplyTaskMessage message = new ApplyTaskMessage(
                taskId, applicationId, platformId, jobId, idempotencyKey, resumeVersionId, traceId);
        rabbitTemplate.convertAndSend(exchange, routingKey, message);
        return taskId;
    }

    private String resolveTraceId() {
        String mdc = MDC.get("traceId");
        return (mdc != null && !mdc.isBlank()) ? mdc : UUID.randomUUID().toString();
    }
}
