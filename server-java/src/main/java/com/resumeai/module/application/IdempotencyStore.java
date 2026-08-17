package com.resumeai.module.application;

/**
 * 幂等键存储（请求级 · 对齐 HLD §4.2 / ADR-006）。
 * <p>SETNX 语义：同一 key 重复写入返回首次值，调用方可据此去重（防客户端网络重试重放）。</p>
 * <p>TODO(P0→生产): 当前由 {@link InMemoryIdempotencyStore} 内存实现；
 * 生产须替换为 Redis {@code SET key value NX}（多实例共享 + 过期），见 HLD §3.4 依赖。</p>
 */
public interface IdempotencyStore {

    /**
     * 若 key 不存在则写入 value 并返回 null；若已存在返回旧值（去重信号）。
     */
    String putIfAbsent(String key, String value);

    String get(String key);
}
