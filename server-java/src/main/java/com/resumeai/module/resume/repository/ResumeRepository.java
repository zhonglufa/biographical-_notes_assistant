package com.resumeai.module.resume.repository;

import com.resumeai.module.resume.entity.Resume;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/** 简历头部仓储（resume）。 */
@Repository
public interface ResumeRepository extends JpaRepository<Resume, Long> {
    Optional<Resume> findByUserIdAndId(String userId, Long id);
}
