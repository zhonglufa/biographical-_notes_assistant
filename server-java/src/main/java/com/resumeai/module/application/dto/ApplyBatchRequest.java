package com.resumeai.module.application.dto;

import java.util.List;

/**
 * A09 批量投递请求体（对齐 HLD §4.2）。
 * <ul>
 *   <li>jobIds: 1..50 个岗位 id；</li>
 *   <li>resumeVersionId: 可选，使用的简历版本；</li>
 *   <li>idempotencyKey: <b>请求级</b> UUID（前端生成），防客户端网络重试重放；
 *       与业务级四元组 (user_id,platform,job_id,apply_date) 正交（见 HLD §4.2 注释）。</li>
 * </ul>
 */
public record ApplyBatchRequest(
        List<String> jobIds,
        String resumeVersionId,
        String idempotencyKey
) {
}
