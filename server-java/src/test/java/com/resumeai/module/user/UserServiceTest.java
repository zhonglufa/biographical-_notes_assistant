package com.resumeai.module.user;

import com.resumeai.common.BizException;
import com.resumeai.module.user.dto.*;
import com.resumeai.security.JwtTokenSigner;
import com.resumeai.security.JwtVerifier;
import com.resumeai.security.UserContext;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.security.KeyPair;
import java.security.KeyPairGenerator;

import static org.junit.jupiter.api.Assertions.*;

/**
 * UserServiceImpl 纯逻辑单测（不启动 Spring context，避免依赖 Redis/RabbitMQ/MySQL 连接）。
 * 2026-08-19 更新：覆盖「mock token → 真实 RS256」后的自签自验行为。
 */
public class UserServiceTest {

    private JwtTokenSigner signer;
    private JwtVerifier verifier;
    private UserServiceImpl svc;

    @BeforeEach
    void setUp() throws Exception {
        KeyPairGenerator g = KeyPairGenerator.getInstance("RSA");
        g.initialize(2048);
        KeyPair kp = g.generateKeyPair();
        signer = new JwtTokenSigner(kp.getPrivate(), "resumeai", 3600, 86400);
        verifier = new JwtVerifier(kp.getPublic(), "resumeai");
        svc = new UserServiceImpl(signer, verifier);
    }

    @Test
    void login_returns_real_jwt_and_plan() {
        LoginResponse r = svc.login(new LoginRequest("a@b.com", "pwd", "email"));
        assertNotNull(r.token());
        assertFalse(r.token().startsWith("mock-"), "应为真实 RS256 JWT，而非 mock 前缀");
        assertEquals("free", r.plan());
        assertNotNull(r.permissions());
        // 自签自验：验签通过且 subject=account
        UserContext ctx = verifier.verify("Bearer " + r.token());
        assertEquals("a@b.com", ctx.userId());
        // refresh 亦为 JWT
        assertFalse(r.refreshToken().startsWith("mock-"));
    }

    @Test
    void login_rejects_empty() {
        assertThrows(BizException.class, () -> svc.login(new LoginRequest(null, null, "email")));
    }

    @Test
    void refresh_reissues_real_jwt() {
        LoginResponse first = svc.login(new LoginRequest("u@x.com", "p", "email"));
        LoginResponse refreshed = svc.refresh(new RefreshRequest(first.refreshToken()));
        assertFalse(refreshed.token().startsWith("mock-"));
        UserContext ctx = verifier.verify("Bearer " + refreshed.token());
        assertEquals("u@x.com", ctx.userId());
    }

    @Test
    void me_resolves_plan_from_verified_sub() {
        LoginResponse r = svc.login(new LoginRequest("u@x.com", "p", "email"));
        UserContext ctx = verifier.verify("Bearer " + r.token());
        UserMeResponse me = svc.me(ctx.userId());
        assertEquals("free", me.plan());
    }
}
