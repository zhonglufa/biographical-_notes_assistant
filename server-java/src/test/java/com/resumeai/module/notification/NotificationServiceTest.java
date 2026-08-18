package com.resumeai.module.notification;

import com.resumeai.module.notification.dto.*;
import com.resumeai.module.notification.service.NotificationService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import static org.junit.jupiter.api.Assertions.*;

/** A22/A23 关键路径单测（H2 内存库 · 对齐 P0/P1 范式）。 */
@SpringBootTest
@ActiveProfiles("test")
class NotificationServiceTest {

    @Autowired
    private NotificationService svc;

    @Test
    void 列表_空用户返回空与0未读() {
        NotificationsListResponse r = svc.list("u-empty");
        assertNotNull(r.items());
        assertEquals(0, r.unread());
    }

    @Test
    void wsUrl_返回wss地址与有效期() {
        WsUrlResponse r = svc.wsUrl("u-1");
        assertTrue(r.wsUrl().startsWith("wss://"));
        assertNotNull(r.expiresIn());
    }
}
