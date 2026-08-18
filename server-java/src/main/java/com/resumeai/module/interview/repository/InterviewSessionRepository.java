package com.resumeai.module.interview.repository;

import com.resumeai.module.interview.entity.InterviewSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface InterviewSessionRepository extends JpaRepository<InterviewSession, Long> {
    Optional<InterviewSession> findByUserIdAndId(String userId, Long id);
}
