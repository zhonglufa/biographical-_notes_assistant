package com.resumeai.module.jobs.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.jobs.entity.JobMatch;
import org.springframework.stereotype.Repository;


/** 匹配度缓存仓储（job_match）。 */
@Repository
public interface JobMatchRepository extends BaseMapper<JobMatch> {


    default JobMatch save(JobMatch e) {
        QueryWrapper<JobMatch> q = new QueryWrapper<JobMatch>()
                .eq("user_id", e.getUserId()).eq("job_id", e.getJobId());
        if (selectOne(q) != null) {
            update(e, new UpdateWrapper<JobMatch>()
                    .eq("user_id", e.getUserId()).eq("job_id", e.getJobId()));
        } else {
            insert(e);
        }
        return e;
    }
    default Optional<JobMatch> findByUserIdAndJobId(String userId, Long jobId) {
        return Optional.ofNullable(selectOne(new QueryWrapper<JobMatch>().eq("user_id", userId).eq("job_id", jobId)));
    }

}
