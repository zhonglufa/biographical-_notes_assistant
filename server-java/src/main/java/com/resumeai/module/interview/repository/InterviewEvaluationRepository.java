package com.resumeai.module.interview.repository;

import com.resumeai.module.interview.entity.InterviewEvaluation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface InterviewEvaluationRepository extends JpaRepository<InterviewEvaluation, Long> {
    Optional<InterviewEvaluation> findBySessionId(Long sessionId);
}
