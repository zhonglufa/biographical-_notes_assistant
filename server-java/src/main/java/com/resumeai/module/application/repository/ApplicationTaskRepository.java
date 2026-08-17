package com.resumeai.module.application.repository;

import com.resumeai.module.application.entity.ApplicationTask;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface ApplicationTaskRepository extends JpaRepository<ApplicationTask, String> {

    Optional<ApplicationTask> findByApplicationId(String applicationId);
}
