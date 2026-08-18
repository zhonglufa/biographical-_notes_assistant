package com.resumeai.module.application;

import org.springframework.stereotype.Component;

import java.util.concurrent.ConcurrentHashMap;

/**
 * 幂等键存储的内存实现（P0 骨架，用于编译/单测/本地验证）。
 * TODO(P0→生产): 替换为 Redis SETNX 实现（多实例共享 + TTL）。
 */
@Component
public class InMemoryIdempotencyStore implements IdempotencyStore {

    private final ConcurrentHashMap<String, String> store = new ConcurrentHashMap<>();

    @Override
    public String putIfAbsent(String key, String value) {
        return store.putIfAbsent(key, value);
    }

    @Override
    public String get(String key) {
        return store.get(key);
    }
}
