package com.resumeai.module.adapter.repository;

import com.resumeai.module.adapter.entity.UserAdapter;
import com.resumeai.module.adapter.entity.UserAdapterId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/** 用户 × 适配器启停态（user_adapter）。 */
@Repository
public interface UserAdapterRepository extends JpaRepository<UserAdapter, UserAdapterId> {
    Optional<UserAdapter> findByUserIdAndPlatformId(String userId, String platformId);
}
