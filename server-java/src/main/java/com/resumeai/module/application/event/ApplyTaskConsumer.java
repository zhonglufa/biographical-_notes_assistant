package com.resumeai.module.application.event;

import com.resumeai.config.ApplyTaskPublisherConfig;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.concurrent.TimeUnit;

/**
 * 投递任务消费者（P1 余下职责，ADR-004 / HLD §3.4.1 C2）。
 *
 * <p>仅 {@code resumeai.mq.mode=rabbit} 时装配（memory 模式不启用监听器）。
 * 监听 {@code apply.task.queue}，消费 {@link ApplyTaskMessage} 后**派发本机 Agent**
 * （服务端不持 Cookie/平台凭据，Cookie 由用户机器上的本机 Agent 本地加载）。</p>
 *
 * <p>幂等：以 {@code idempotencyKey + taskId} 为键在 Redis 去重，重复消息直接跳过，避免重复投递。
 * 派发失败（本机 Agent 不可达/非 2xx）抛异常 → 由队列的死信交换机 {@code apply.dlx} 路由到 DLQ 重试。</p>
 *
 * <p>⚠️ 偏差（诚实标注）：本机 Agent 的 HTTP 回调契约（路径/请求体/响应）仅服务端定义，端到端联调
 * 需用户机器上的客户端配合，属待办（B-2）。</p>
 */
@Component
@ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
public class ApplyTaskConsumer {

    private static final Logger log = LoggerFactory.getLogger(ApplyTaskConsumer.class);
    private static final String IDEMPOTENCY_PREFIX = "apply-task:idem:";
    private static final long IDEMPOTENCY_TTL_SECONDS = 86_400L;

    private final StringRedisTemplate redis;
    private final RestTemplate rest;
    private final String agentCallbackBaseUrl;

    public ApplyTaskConsumer(StringRedisTemplate redis,
                             RestTemplate rest,
                             @Value("${resumeai.agent.callback-base-url:http://localhost:9800}") String agentCallbackBaseUrl) {
        this.redis = redis;
        this.rest = rest;
        this.agentCallbackBaseUrl = agentCallbackBaseUrl;
    }

    @RabbitListener(queues = ApplyTaskPublisherConfig.QUEUE)
    public void onMessage(ApplyTaskMessage msg) {
        String idemKey = IDEMPOTENCY_PREFIX + msg.idempotencyKey() + ":" + msg.taskId();

        if (redis != null && Boolean.TRUE.equals(redis.hasKey(idemKey))) {
            log.info("跳过重复投递任务 taskId={}（幂等键已存在）", msg.taskId());
            return;
        }

        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<ApplyTaskMessage> entity = new HttpEntity<>(msg, headers);
            ResponseEntity<String> resp = rest.postForEntity(
                    agentCallbackBaseUrl + "/tasks", entity, String.class);
            if (resp.getStatusCode().is2xxSuccessful()) {
                if (redis != null) {
                    redis.opsForValue().set(idemKey, "1");
                    redis.expire(idemKey, IDEMPOTENCY_TTL_SECONDS, TimeUnit.SECONDS);
                }
                log.info("已派发投递任务 taskId={} 至本机 Agent {}", msg.taskId(), agentCallbackBaseUrl);
            } else {
                throw new IllegalStateException("本机 Agent 派发返回非 2xx: HTTP " + resp.getStatusCode());
            }
        } catch (Exception e) {
            log.error("派发投递任务失败 taskId={}，将路由至死信队列: {}", msg.taskId(), e.getMessage());
            throw e; // 抛出让 RabbitMQ 按 apply.dlx 路由到 DLQ
        }
    }
}
