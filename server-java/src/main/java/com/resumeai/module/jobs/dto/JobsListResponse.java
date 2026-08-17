package com.resumeai.module.jobs.dto;

import java.util.List;

/** A07 响应（对齐 jobs-list.response.schema.json）：items + total + page + pageSize。 */
public record JobsListResponse(List<JobStub> items, long total, int page, int pageSize) {
}
