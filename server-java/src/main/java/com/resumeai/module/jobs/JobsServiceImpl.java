package com.resumeai.module.jobs;

import com.resumeai.common.BizException;
import com.resumeai.module.jobs.dto.FavoriteRequest;
import com.resumeai.module.jobs.dto.FavoriteResponse;
import com.resumeai.module.jobs.dto.JobStub;
import com.resumeai.module.jobs.dto.JobsListResponse;
import com.resumeai.module.jobs.entity.Job;
import com.resumeai.module.jobs.entity.JobFavorite;
import com.resumeai.module.jobs.entity.JobMatch;
import com.resumeai.module.jobs.repository.JobFavoriteRepository;
import com.resumeai.module.jobs.repository.JobMatchRepository;
import com.resumeai.module.jobs.repository.JobRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * 岗位浏览业务实现（A07 / A08 · 对齐 LLD-岗位浏览模块 §1/§3）。
 *
 * <p>防生产事故约束：
 * <ul>
 *   <li>只读岗位：不抓取、不投递（HLD §3.3 边界）；</li>
 *   <li>匹配度反范式读取：列表不逐条同步调 B01（否则 N×≤5s 不可接受），只回读 job_match 缓存，缺失为 null；</li>
 *   <li>数据隔离：收藏按 user_id 归属，越权访问返回 404（RESOURCE_NOT_FOUND）；</li>
 *   <li>幂等：重复同动作无副作用。</li>
 * </ul>
 */
@Service
public class JobsServiceImpl implements JobsService {

    private final JobRepository jobRepo;
    private final JobMatchRepository matchRepo;
    private final JobFavoriteRepository favRepo;

    public JobsServiceImpl(JobRepository jobRepo, JobMatchRepository matchRepo, JobFavoriteRepository favRepo) {
        this.jobRepo = jobRepo;
        this.matchRepo = matchRepo;
        this.favRepo = favRepo;
    }

    @Override
    public JobsListResponse search(String userId, String keyword, String location, String platform,
                                   Integer salaryMin, int page, int pageSize) {
        int page0 = Math.max(page - 1, 0);
        Page<Job> pageRes = jobRepo.search(keyword, location, platform, salaryMin, PageRequest.of(page0, pageSize));

        List<JobStub> items = new ArrayList<>();
        for (Job j : pageRes.getContent()) {
            Integer matchScore = null;
            String matchBand = null;
            String matchReason = null;
            Optional<JobMatch> m = matchRepo.findByUserIdAndJobId(userId, j.getId());
            if (m.isPresent()) {
                matchScore = m.get().getScore();
                matchBand = m.get().getBand();
                matchReason = m.get().getReason();
            }
            boolean favorited = favRepo.findByUserIdAndJobId(userId, j.getId())
                    .map(f -> "favorite".equals(f.getAction()))
                    .orElse(false);

            items.add(new JobStub(
                    String.valueOf(j.getId()),
                    j.getTitle(),
                    j.getCompany(),
                    j.getPlatformId(),
                    j.getSalaryMin(),
                    j.getSalaryMax(),
                    j.getLocation(),
                    j.getSource(),
                    matchScore,
                    matchBand,
                    matchReason,
                    favorited,
                    j.getCollectedAt()));
        }
        return new JobsListResponse(items, pageRes.getTotalElements(), page, pageSize);
    }

    @Override
    public FavoriteResponse favorite(String userId, String jobId, FavoriteRequest req) {
        Long jobIdL;
        try {
            jobIdL = Long.valueOf(jobId);
        } catch (NumberFormatException e) {
            throw new BizException(404, "RESOURCE_NOT_FOUND");
        }
        if (jobRepo.findById(jobIdL).isEmpty()) {
            throw new BizException(404, "RESOURCE_NOT_FOUND");
        }
        String action = req.action();
        if (!"favorite".equals(action) && !"ignore".equals(action)) {
            throw new BizException(400, "INVALID_ACTION");
        }

        JobFavorite fav = favRepo.findByUserIdAndJobId(userId, jobIdL).orElse(null);
        if (fav == null) {
            fav = new JobFavorite();
            fav.setUserId(userId);
            fav.setJobId(jobIdL);
        }
        fav.setAction(action);
        fav.setCreatedAt(System.currentTimeMillis());
        favRepo.save(fav);

        String status = "favorite".equals(action) ? "favorited" : "ignored";
        String favoriteId = "favorite".equals(action) ? String.valueOf(jobIdL) : null;
        return new FavoriteResponse(true, favoriteId, status);
    }
}
