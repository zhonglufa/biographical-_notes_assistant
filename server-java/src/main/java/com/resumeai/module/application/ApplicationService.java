package com.resumeai.module.application;

import com.resumeai.module.application.dto.*;

/**
 * 投递模块业务接口（A09 批量投递 / A10 列表 / A11 详情）。
 * 实现须严格对齐 HLD §3.4 / §4.2 / §4.3 + LLD-投递状态机 v1.0。
 */
public interface ApplicationService {

    /** A09 批量投递：双层幂等 + 角色日限额 + 202 Accepted。 */
    ApplyBatchResponse applyBatch(String userId, ApplyBatchRequest req);

    /** A10 投递列表（本人数据隔离）。 */
    ApplicationsListResponse list(String userId);

    /** A11 投递详情（状态机当前态 + 时间线）；越权返回 404 不泄露归属。 */
    ApplicationDetailResponse detail(String userId, String id);
}
