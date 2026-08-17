package com.resumeai.module.jobs.dto;

/**
 * A07 岗位列表单项（jobStub · 对齐 jobs-list.response.schema.json）。
 * matchScore / matchBand / matchReason / favorited 缺失为 null（反范式缓存未计算时）。
 */
public record JobStub(
        String jobId,
        String title,
        String company,
        String platformId,
        Integer salaryMin,
        Integer salaryMax,
        String location,
        String source,
        Integer matchScore,
        String matchBand,
        String matchReason,
        Boolean favorited,
        Long collectedAt) {
}
