package com.resumeai.module.application;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 10 态投递状态机单元测试（纯函数，不连库）。
 * 矩阵须与 Python delivery_state_machine.TRANSITIONS 及 HLD §3.4 / ADR-008 完全一致（双语言不漂移）。
 */
class DeliveryStateMachineTest {

    @Test
    void 合法转移_初始到执行() {
        DeliveryStateMachine.assertTransition("pending_confirm", "autofilling");
    }

    @Test
    void 合法转移_终态归档() {
        DeliveryStateMachine.assertTransition("offer", "closed");
    }

    @Test
    void 自环_抛异常() {
        assertThrows(IllegalArgumentException.class,
                () -> DeliveryStateMachine.assertTransition("submitted", "submitted"));
    }

    @Test
    void 回退边_抛异常() {
        assertThrows(IllegalArgumentException.class,
                () -> DeliveryStateMachine.assertTransition("viewed", "submitted"));
    }

    @Test
    void 终态再转_抛异常() {
        assertThrows(IllegalArgumentException.class,
                () -> DeliveryStateMachine.assertTransition("closed", "submitted"));
    }

    @Test
    void 未知目标态_抛异常() {
        assertThrows(IllegalArgumentException.class,
                () -> DeliveryStateMachine.assertTransition("pending_confirm", "unknown_state"));
    }

    @Test
    void 业务幂等键格式_四元组() {
        assertEquals("u|p|j|2026-08-18",
                DeliveryStateMachine.businessIdempotencyKey("u", "p", "j", "2026-08-18"));
    }

    @Test
    void 终态判定() {
        assertTrue(DeliveryStateMachine.isTerminal("closed"));
        assertTrue(DeliveryStateMachine.isTerminal("rejected"));
        assertFalse(DeliveryStateMachine.isTerminal("submitted"));
    }
}
