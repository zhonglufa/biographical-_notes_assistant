package com.resumeai.module.adapter.client;

/**
 * 本机 Agent ↔ 服务端 RPC 客户端（编排侧）。
 *
 * <p>红线（HLD §3.6 / ADR-003）：服务端经此接口向<b>用户本机 desktop-agent</b>下发指令
 * （B06/B08/B09/B10/B11 任务通道），<b>绝不直连招聘平台、绝不持有平台 Cookie</b>。
 * 真实实现为 WSS 双向 RPC（agent-server-rpc.registry.schema.json）；当前为内存桩。
 */
public interface AgentRpcClient {

    /** 下发适配器启停指令到本机 Agent。 */
    void sendAdapterEnableCommand(String userId, String platformId, boolean enabled);
}
