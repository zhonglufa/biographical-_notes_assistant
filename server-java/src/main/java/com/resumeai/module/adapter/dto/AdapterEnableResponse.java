package com.resumeai.module.adapter.dto;

/** A15 响应（对齐 adapter-enable.response.schema.json）：adapterId + status(enabled|disabled)。 */
public record AdapterEnableResponse(String adapterId, String status) {
}
