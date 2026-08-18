package com.resumeai.module.adapter;

import com.resumeai.module.adapter.client.AgentRpcClient;
import com.resumeai.module.adapter.dto.AdapterEnableResponse;
import com.resumeai.module.adapter.dto.AdapterInfo;
import com.resumeai.module.adapter.dto.AdaptersListResponse;
import com.resumeai.module.adapter.entity.AdapterRegistry;
import com.resumeai.module.adapter.entity.UserAdapter;
import com.resumeai.module.adapter.repository.AdapterRegistryRepository;
import com.resumeai.module.adapter.repository.UserAdapterRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 适配器编排业务实现（A14 / A15 · 对齐 LLD-平台适配器系统 §3）。
 *
 * <p>防生产事故红线（HLD §3.6 / ADR-003）：
 * <ul>
 *   <li>服务端只编排：存适配器元数据 + 用户启停态，经 {@link AgentRpcClient} 下发本机 Agent 指令；</li>
 *   <li>绝不直连招聘平台、绝不持有/上传平台 Cookie（Cookie 仅存于本机，加密）；</li>
 *   <li>不定义业务状态机（投递 10 态机在 application 模块）；本模块只管生命周期 installed/test_mode/enabled/disabled。</li>
 * </ul>
 */
@Service
public class AdapterServiceImpl implements AdapterService {

    private final AdapterRegistryRepository registryRepo;
    private final UserAdapterRepository userAdapterRepo;
    private final AgentRpcClient agentRpc;

    public AdapterServiceImpl(AdapterRegistryRepository registryRepo,
                              UserAdapterRepository userAdapterRepo,
                              AgentRpcClient agentRpc) {
        this.registryRepo = registryRepo;
        this.userAdapterRepo = userAdapterRepo;
        this.agentRpc = agentRpc;
    }

    @Override
    public AdaptersListResponse list(String userId) {
        List<AdapterRegistry> active = registryRepo.findByStatus("active");
        List<AdapterInfo> items = new ArrayList<>();
        for (AdapterRegistry r : active) {
            boolean enabled = userAdapterRepo.findByUserIdAndPlatformId(userId, r.getPlatformId())
                    .map(UserAdapter::isEnabled)
                    .orElse(true); // 无记录默认启用
            items.add(new AdapterInfo(
                    r.getPlatformId(),
                    r.getPlatformId(),
                    r.getPlatformId(),
                    r.getVersion(),
                    enabled ? "enabled" : "disabled",
                    r.getStatus()));
        }
        return new AdaptersListResponse(items);
    }

    @Override
    public AdapterEnableResponse enable(String userId, String adapterId, boolean enabled) {
        // TODO: pro 套餐校验（仅 pro 可操作，LLD §A15）；当前骨架未接会员体系。
        UserAdapter ua = userAdapterRepo.findByUserIdAndPlatformId(userId, adapterId).orElse(null);
        if (ua == null) {
            ua = new UserAdapter();
            ua.setUserId(userId);
            ua.setPlatformId(adapterId);
        }
        ua.setEnabled(enabled);
        ua.setCreatedAt(System.currentTimeMillis());
        userAdapterRepo.save(ua);

        // 编排：下发本机 Agent 启停指令（服务端不直连平台）
        agentRpc.sendAdapterEnableCommand(userId, adapterId, enabled);

        return new AdapterEnableResponse(adapterId, enabled ? "enabled" : "disabled");
    }
}
