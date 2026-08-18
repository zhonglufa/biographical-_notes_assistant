package com.resumeai.module.notification.service;

import com.resumeai.module.notification.client.NotificationWsClient;
import com.resumeai.module.notification.dto.*;
import com.resumeai.module.notification.entity.Notification;
import com.resumeai.module.notification.repository.NotificationRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class NotificationServiceImpl implements NotificationService {

    private final NotificationRepository repo;
    private final NotificationWsClient wsClient;

    public NotificationServiceImpl(NotificationRepository repo, NotificationWsClient wsClient) {
        this.repo = repo;
        this.wsClient = wsClient;
    }

    @Override
    public NotificationsListResponse list(String userId) {
        List<Notification> list = repo.findByUserIdOrderByCreatedAtDesc(userId);
        List<NotificationItem> items = list.stream().map(n -> new NotificationItem(
                String.valueOf(n.getId()), n.getLevel(), n.getTitle(), n.getBody(),
                n.isReadFlag(), n.getCreatedAt(), n.getChannel()
        )).collect(Collectors.toList());
        int unread = repo.countByUserIdAndReadFlagFalse(userId);
        return new NotificationsListResponse(items, unread);
    }

    @Override
    public WsUrlResponse wsUrl(String userId) {
        return new WsUrlResponse(wsClient.generateWsUrl(userId), 3600);
    }
}
