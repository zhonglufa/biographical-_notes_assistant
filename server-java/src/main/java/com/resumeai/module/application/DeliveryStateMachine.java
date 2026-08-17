package com.resumeai.module.application;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 10 态投递状态机（Java 侧中枢 · 对齐 HLD §3.4 / ADR-008 / LLD-投递状态机 v1.0 / Python delivery_state_machine.py）。
 *
 * <p>设计要点（不可偏离）：
 * <ul>
 *   <li>无回退边（如 viewd 不可回 submitted）；</li>
 *   <li>{@code rejected}/{@code closed} 为终态，不可再转移；</li>
 *   <li>所有转移由调用方写审计日志（{@code ApplicationEvent}），本类只做矩阵裁决、不持有数据；</li>
 *   <li>矩阵与 Python 草稿 {@code delivery_state_machine.TRANSITIONS} 严格一致，双语言不漂移。</li>
 * </ul>
 *
 * <p>注意：本类为纯函数式裁决器，状态数据存于 {@code Application} 实体；避免与生产事故相关的
 * 「状态错乱」——任何转移必须先经 {@link #assertTransition(String, String)} 校验。</p>
 */
public final class DeliveryStateMachine {

    /** 终态集合（不可再转移）。 */
    public static final Set<String> TERMINAL = Set.of("rejected", "closed");

    /** 10 态枚举（顺序即 UI 展示/演进序）。 */
    public static final List<String> STATES = List.of(
            "pending_confirm", "autofilling", "submitted", "viewed", "contacting",
            "interview_invited", "interview_done", "offer", "rejected", "closed");

    /** 允许转移矩阵：当前态 -> 可到达的下一态集合（对齐 ADR-008 + LLD §1）。 */
    private static final Map<String, Set<String>> TRANSITIONS = new HashMap<>();

    static {
        TRANSITIONS.put("pending_confirm", Set.of("autofilling"));
        TRANSITIONS.put("autofilling", Set.of("submitted", "closed", "pending_confirm"));
        TRANSITIONS.put("submitted", Set.of("viewed", "rejected", "closed"));
        TRANSITIONS.put("viewed", Set.of("contacting", "rejected", "closed"));
        TRANSITIONS.put("contacting", Set.of("interview_invited", "rejected", "closed"));
        TRANSITIONS.put("interview_invited", Set.of("interview_done", "rejected", "closed"));
        TRANSITIONS.put("interview_done", Set.of("offer", "rejected", "closed"));
        TRANSITIONS.put("offer", Set.of("closed"));
        TRANSITIONS.put("rejected", Set.of());
        TRANSITIONS.put("closed", Set.of());
    }

    private DeliveryStateMachine() {
    }

    /** 是否为终态。 */
    public static boolean isTerminal(String state) {
        return TERMINAL.contains(state);
    }

    /** 当前态是否允许转移到目标态（不含自环判定）。 */
    public static boolean canTransition(String from, String to) {
        if (from == null || to == null) {
            return false;
        }
        return TRANSITIONS.getOrDefault(from, Set.of()).contains(to);
    }

    /**
     * 校验转移合法性，非法抛 {@link IllegalArgumentException}。
     * 覆盖：未知态 / 自环 / 回退边 / 终态再转 / 矩阵外转移。
     */
    public static void assertTransition(String from, String to) {
        if (!STATES.contains(from)) {
            throw new IllegalArgumentException("未知当前态: " + from);
        }
        if (!STATES.contains(to)) {
            throw new IllegalArgumentException("未知目标态: " + to);
        }
        if (from.equals(to)) {
            throw new IllegalArgumentException("自环不允许: " + from + "->" + to);
        }
        if (!canTransition(from, to)) {
            throw new IllegalArgumentException("非法转移(无回退边/矩阵外): " + from + "->" + to);
        }
    }

    /** 业务级幂等四元组（ADR-006 / HLD §6.13.2）：防「同用户同日对同岗」重投命门。 */
    public static String businessIdempotencyKey(String userId, String platformId, String jobId, String applyDate) {
        return userId + "|" + platformId + "|" + jobId + "|" + applyDate;
    }
}
