package com.resumeai.module.application.event;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ApplyTaskConsumerTest {

    @Mock
    private StringRedisTemplate redis;
    @Mock
    private ValueOperations<String, String> valueOps;
    @Mock
    private RestTemplate rest;

    private ApplyTaskConsumer consumer;

    @BeforeEach
    void setUp() {
        consumer = new ApplyTaskConsumer(redis, rest, "http://agent.local:9800");
        // 仅成功派发用例会走到 redis.opsForValue()；skip/failure 用例提前返回，标记 lenient 避免严格桩报错
        lenient().when(redis.opsForValue()).thenReturn(valueOps);
    }

    @Test
    void dispatches_to_local_agent_and_records_idempotency() {
        when(redis.hasKey(anyString())).thenReturn(false);
        when(rest.postForEntity(eq("http://agent.local:9800/tasks"), any(HttpEntity.class), eq(String.class)))
                .thenReturn(ResponseEntity.ok("accepted"));

        ApplyTaskMessage msg = new ApplyTaskMessage("t1", "a1", "p1", "j1", "idem-1", "rv1", "trace-1");
        consumer.onMessage(msg);

        verify(rest).postForEntity(eq("http://agent.local:9800/tasks"), any(HttpEntity.class), eq(String.class));
        verify(valueOps).set(anyString(), eq("1"));
        // 主代码直接调用 StringRedisTemplate.expire(K,long,TimeUnit)，幂等键 TTL 由此设置
        verify(redis).expire(anyString(), eq(86_400L), eq(TimeUnit.SECONDS));
    }

    @Test
    void skips_when_idempotency_key_present() {
        when(redis.hasKey(anyString())).thenReturn(true);

        ApplyTaskMessage msg = new ApplyTaskMessage("t1", "a1", "p1", "j1", "idem-1", "rv1", "trace-1");
        consumer.onMessage(msg);

        verify(rest, never()).postForEntity(anyString(), any(), any());
    }

    @Test
    void dispatch_failure_throws_to_route_dlq() {
        when(redis.hasKey(anyString())).thenReturn(false);
        when(rest.postForEntity(anyString(), any(), any())).thenThrow(new RuntimeException("agent down"));

        ApplyTaskMessage msg = new ApplyTaskMessage("t1", "a1", "p1", "j1", "idem-1", "rv1", "trace-1");
        assertThrows(RuntimeException.class, () -> consumer.onMessage(msg));
    }
}
