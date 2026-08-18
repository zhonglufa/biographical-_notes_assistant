package com.resumeai.module.notification.repository;

import com.resumeai.module.notification.entity.Notification;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface NotificationRepository extends JpaRepository<Notification, Long> {
    List<Notification> findByUserIdOrderByCreatedAtDesc(String userId);

    int countByUserIdAndReadFlagFalse(String userId);
}
