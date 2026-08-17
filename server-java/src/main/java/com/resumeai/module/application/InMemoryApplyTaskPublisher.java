package com.resumeai.module.application;

import org.springframework.stereotype.Component;

import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 投递任务下发器的内存实现（P0 骨架）。仅记录下发，不真正触达本机 Agent。
 * TODO(P0→生产): 替换为 RabbitMQ 发布（ADR-004）。
 */
@Component
public class InMemoryApplyTaskPublisher implements ApplyTaskPublisher {

    private final ConcurrentHashMap<String, String> published = new ConcurrentHashMap<>();

    @Override
    public String publish(String applicationId, String platformId, String jobId,
                          String idempotencyKey, String resumeVersionId) {
        String taskId = UUID.randomUUID().toString();
        published.put(taskId, applicationId);
        return taskId;
    }
}
