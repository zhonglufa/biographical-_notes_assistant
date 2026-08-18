package com.resumeai.module.resume;

import com.resumeai.module.resume.dto.AtsScoreRequest;
import com.resumeai.module.resume.dto.AtsScoreResponse;
import com.resumeai.module.resume.dto.ResumeCreateRequest;
import com.resumeai.module.resume.dto.ResumeCreateResponse;
import com.resumeai.module.resume.dto.ResumeDiffRequest;
import com.resumeai.module.resume.dto.ResumeDiffResponse;
import com.resumeai.module.resume.dto.ResumeVersionsResponse;

/** 简历工作台业务接口（A04 / A05 / A06）。 */
public interface ResumeService {

    /** A04 创建简历（落首个版本快照，preferred 指向它）。 */
    ResumeCreateResponse create(String userId, ResumeCreateRequest req);

    /** A05 版本列表（含 diffAvailable）。 */
    ResumeVersionsResponse listVersions(String userId, String resumeId);

    /** A05 版本结构化 diff（字段级 added/removed/modified）。 */
    ResumeDiffResponse diff(String userId, String resumeId, ResumeDiffRequest req);

    /** A06 触发 ATS 评分（异步，锁版本；返回 taskId + pending）。 */
    AtsScoreResponse atsScore(String userId, AtsScoreRequest req);
}
