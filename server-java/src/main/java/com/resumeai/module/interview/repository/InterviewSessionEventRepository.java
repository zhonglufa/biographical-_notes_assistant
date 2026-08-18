package com.resumeai.module.interview.repository;

import com.resumeai.module.interview.entity.InterviewSessionEvent;
import org.springframework.data.jpa.repository.JpaRepository;

public interface InterviewSessionEventRepository extends JpaRepository<InterviewSessionEvent, Long> {
}
