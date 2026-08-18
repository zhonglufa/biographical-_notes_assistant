package com.resumeai.module.adapter.client;

import org.springframework.stereotype.Component;

/**
 * AgentRpcClient 内存桩（CI / 本地无本机 Agent 时使用）。
 * TODO：替换为 WSS 双向 RPC 实现（agent-server-rpc.registry.schema.json），
 * 经任务通道下发到本机 desktop-agent；服务端不直连平台、不上传 Cookie。
 */
@Component
public class InMemoryAgentRpcClient implements AgentRpcClient {

    @Override
    public void sendAdapterEnableCommand(String userId, String platformId, boolean enabled) {
        // 内存桩：仅记录调用意图，不发起任何网络/平台请求。
        // TODO: 经 WSS 下发 enable/disable 指令到本机 Agent 的 adapter 生命周期方法（adapter-facade.methods.json）。
    }
}
