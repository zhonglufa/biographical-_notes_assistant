package com.resumeai.module.jobs;

import com.resumeai.module.jobs.dto.FavoriteRequest;
import com.resumeai.module.jobs.dto.FavoriteResponse;
import com.resumeai.module.jobs.dto.JobsListResponse;

/** 岗位浏览业务接口（A07 / A08）。 */
public interface JobsService {

    /** A07 聚合搜索（只读岗位 + 读匹配度缓存 + 当前用户收藏标记）。 */
    JobsListResponse search(String userId, String keyword, String location, String platform,
                            Integer salaryMin, int page, int pageSize);

    /** A08 收藏 / 忽略（幂等；ignore 供投递推荐过滤）。 */
    FavoriteResponse favorite(String userId, String jobId, FavoriteRequest req);
}
