package com.resumeai.module.application.repository;

import com.resumeai.module.application.entity.ApplicationEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ApplicationEventRepository extends JpaRepository<ApplicationEvent, String> {

    List<ApplicationEvent> findByApplicationIdOrderByOccurredAtAsc(String applicationId);
}
