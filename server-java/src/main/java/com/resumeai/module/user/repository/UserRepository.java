package com.resumeai.module.user.repository;

import com.resumeai.module.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * 用户仓储（仅 Java 直连业务库，ADR-002 存储解耦）。
 */
public interface UserRepository extends JpaRepository<User, Long> {
    User findByEmail(String email);
}
