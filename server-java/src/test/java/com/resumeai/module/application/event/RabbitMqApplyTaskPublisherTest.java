package com.resumeai.module.application.event;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class RabbitMqApplyTaskPublisherTest {

    private static final String EXCHANGE = "apply.direct";
    private static final String ROUTING_KEY = "apply.task";

    @Mock
    private RabbitTemplate rabbitTemplate;

    private RabbitMqApplyTaskPublisher publisher;

    @BeforeEach
    void setUp() {
        // 必须在 Mockito 完成 @Mock 注入后再构造被测对象，否则 rabbitTemplate 为 null
        publisher = new RabbitMqApplyTaskPublisher(rabbitTemplate, EXCHANGE, ROUTING_KEY);
    }

    @Test
    void publishSendsMessageToExchangeWithRoutingKeyAndTraceId() {
        String taskId = publisher.publish("app-1", "plat-1", "job-1", "idem-1", "rv-1");

        assertNotNull(taskId);
        ArgumentCaptor<ApplyTaskMessage> captor = ArgumentCaptor.forClass(ApplyTaskMessage.class);
        verify(rabbitTemplate).convertAndSend(eq(EXCHANGE), eq(ROUTING_KEY), captor.capture());

        ApplyTaskMessage msg = captor.getValue();
        assertEquals("app-1", msg.applicationId());
        assertEquals("plat-1", msg.platformId());
        assertEquals("job-1", msg.jobId());
        assertEquals("idem-1", msg.idempotencyKey());
        assertEquals("rv-1", msg.resumeVersionId());
        assertEquals(taskId, msg.taskId());
        assertNotNull(msg.traceId());
    }
}
