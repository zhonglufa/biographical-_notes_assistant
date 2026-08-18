package com.resumeai.module.adapter.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.adapter.entity.UserAdapter;
import org.springframework.stereotype.Repository;


/** 用户 × 适配器启停态（user_adapter）。 */
@Repository
public interface UserAdapterRepository extends BaseMapper<UserAdapter> {


    default UserAdapter save(UserAdapter e) {
        QueryWrapper<UserAdapter> q = new QueryWrapper<UserAdapter>()
                .eq("user_id", e.getUserId()).eq("platform_id", e.getPlatformId());
        if (selectOne(q) != null) {
            update(e, new UpdateWrapper<UserAdapter>()
                    .eq("user_id", e.getUserId()).eq("platform_id", e.getPlatformId()));
        } else {
            insert(e);
        }
        return e;
    }
    default Optional<UserAdapter> findByUserIdAndPlatformId(String userId, String platformId) {
        return Optional.ofNullable(selectOne(new QueryWrapper<UserAdapter>().eq("user_id", userId).eq("platform_id", platformId)));
    }

}
