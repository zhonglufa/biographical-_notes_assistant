package com.resumeai.module.jobs.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.jobs.entity.JobFavorite;
import org.springframework.stereotype.Repository;


/** 收藏 / 忽略仓储（job_favorite）。 */
@Repository
public interface JobFavoriteRepository extends BaseMapper<JobFavorite> {


    default JobFavorite save(JobFavorite e) {
        QueryWrapper<JobFavorite> q = new QueryWrapper<JobFavorite>()
                .eq("user_id", e.getUserId()).eq("job_id", e.getJobId());
        if (selectOne(q) != null) {
            update(e, new UpdateWrapper<JobFavorite>()
                    .eq("user_id", e.getUserId()).eq("job_id", e.getJobId()));
        } else {
            insert(e);
        }
        return e;
    }
    default Optional<JobFavorite> findByUserIdAndJobId(String userId, Long jobId) {
        return Optional.ofNullable(selectOne(new QueryWrapper<JobFavorite>().eq("user_id", userId).eq("job_id", jobId)));
    }

}
