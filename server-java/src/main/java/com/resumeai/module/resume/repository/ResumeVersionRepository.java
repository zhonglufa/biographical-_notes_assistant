package com.resumeai.module.resume.repository;

import com.resumeai.module.resume.entity.ResumeVersion;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/** 简历版本快照仓储（resume_version）。 */
@Repository
public interface ResumeVersionRepository extends JpaRepository<ResumeVersion, Long> {
    List<ResumeVersion> findByResumeIdOrderByVersionNoAsc(Long resumeId);

    Optional<ResumeVersion> findByResumeIdAndId(Long resumeId, Long id);

    Optional<ResumeVersion> findByUserIdAndId(String userId, Long id);
}
