package com.resumeai.module.adapter.dto;

/**
 * A14 适配器列表单项。
 * status = 当前用户启停态（enabled/disabled）；globalStatus = 适配器包全局态（active/deprecated/disabled）。
 * 注：A14 列表响应尚无独立契约 schema（登记为缺口，待补 adapters-list.response.schema.json）。
 */
public record AdapterInfo(
        String adapterId,
        String platform,
        String name,
        String version,
        String status,
        String globalStatus) {
}
