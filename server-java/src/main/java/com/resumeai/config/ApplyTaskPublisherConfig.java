package com.resumeai.config;

import com.resumeai.module.application.ApplyTaskPublisher;
import com.resumeai.module.application.InMemoryApplyTaskPublisher;
import com.resumeai.module.application.event.RabbitMqApplyTaskPublisher;
import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.DirectExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 投递任务发布器 Bean 装配（ADR-004）。
 * <p>通过 {@code resumeai.mq.mode} 在「内存实现」与「RabbitMQ 实现」间切换：
 * <ul>
 *   <li>{@code memory}（默认）：{@link InMemoryApplyTaskPublisher}，不依赖 broker，用于开发/测试；</li>
 *   <li>{@code rabbit}：{@link RabbitMqApplyTaskPublisher} + 交换机/队列/死信拓扑 + JSON 序列化，用于生产。</li>
 * </ul>
 * 默认 memory 模式下 {@code management.health.rabbit.enabled=false}（见 application.yml），
 * 避免本地/测试无 broker 时 /health 误报 rabbit DOWN（属预期，非故障）。生产设
 * {@code MQ_MODE=rabbit} 且 {@code MQ_RABBIT_HEALTH=true} 即启用 broker 健康探活。
 */
@Configuration
public class ApplyTaskPublisherConfig {

    public static final String EXCHANGE = "apply.direct";
    public static final String ROUTING_KEY = "apply.task";
    public static final String QUEUE = "apply.task.queue";
    public static final String DLQ = "apply.task.dlq";
    public static final String DLX = "apply.dlx";
    public static final String DLQ_ROUTING_KEY = "apply.task.dlq";

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public ApplyTaskPublisher rabbitMqApplyTaskPublisher(RabbitTemplate rabbitTemplate) {
        return new RabbitMqApplyTaskPublisher(rabbitTemplate, EXCHANGE, ROUTING_KEY);
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "memory", matchIfMissing = true)
    public ApplyTaskPublisher inMemoryApplyTaskPublisher() {
        return new InMemoryApplyTaskPublisher();
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public MessageConverter applyJsonMessageConverter() {
        return new Jackson2JsonMessageConverter();
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public DirectExchange applyExchange() {
        return new DirectExchange(EXCHANGE, true, false);
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public DirectExchange applyDlx() {
        return new DirectExchange(DLX, true, false);
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public Queue applyQueue() {
        return QueueBuilder.durable(QUEUE)
                .withArgument("x-dead-letter-exchange", DLX)
                .withArgument("x-dead-letter-routing-key", DLQ_ROUTING_KEY)
                .build();
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public Queue applyDlq() {
        return QueueBuilder.durable(DLQ).build();
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public Binding applyBinding() {
        return BindingBuilder.bind(applyQueue()).to(applyExchange()).with(ROUTING_KEY);
    }

    @Bean
    @ConditionalOnProperty(name = "resumeai.mq.mode", havingValue = "rabbit")
    public Binding applyDlqBinding() {
        return BindingBuilder.bind(applyDlq()).to(applyDlx()).with(DLQ_ROUTING_KEY);
    }
}
