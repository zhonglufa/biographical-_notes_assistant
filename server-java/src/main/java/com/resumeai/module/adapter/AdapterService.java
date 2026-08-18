package com.resumeai.module.adapter;

import com.resumeai.module.adapter.dto.AdapterEnableResponse;
import com.resumeai.module.adapter.dto.AdaptersListResponse;

/** 适配器编排业务接口（A14 / A15）。 */
public interface AdapterService {

    /** A14 列出当前用户的适配器及启停态（只读 registry + 用户态，不触达平台）。 */
    AdaptersListResponse list(String userId);

    /** A15 启用 / 停用某适配器（编排：写用户态 + 下发本机 Agent 指令）。 */
    AdapterEnableResponse enable(String userId, String adapterId, boolean enabled);
}
