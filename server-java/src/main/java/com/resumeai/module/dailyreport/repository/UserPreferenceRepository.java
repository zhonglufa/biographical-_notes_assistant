package com.resumeai.module.dailyreport.repository;

import com.resumeai.module.dailyreport.entity.UserPreference;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserPreferenceRepository extends JpaRepository<UserPreference, String> {
}
