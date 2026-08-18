package com.resumeai.module.user;

import com.resumeai.common.BizException;
import com.resumeai.module.user.dto.*;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * UserServiceImpl 纯逻辑单测（不启动 Spring context，避免依赖 Redis/RabbitMQ/MySQL 连接）。
 */
public class UserServiceTest {

    @Test
    void login_returns_token_and_plan() {
        UserService svc = new UserServiceImpl();
        LoginResponse r = svc.login(new LoginRequest("a@b.com", "pwd", "email"));
        assertNotNull(r.token());
        assertEquals("free", r.plan());
        assertNotNull(r.permissions());
    }

    @Test
    void login_rejects_empty() {
        UserService svc = new UserServiceImpl();
        assertThrows(BizException.class, () -> svc.login(new LoginRequest(null, null, "email")));
    }

    @Test
    void me_resolves_token() {
        UserService svc = new UserServiceImpl();
        LoginResponse r = svc.login(new LoginRequest("u@x.com", "p", "email"));
        UserMeResponse me = svc.me(r.token());
        assertEquals("free", me.plan());
    }
}
