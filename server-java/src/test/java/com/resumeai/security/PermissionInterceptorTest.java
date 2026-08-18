package com.resumeai.security;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PermissionInterceptor 单元测试（纯函数，不引 Spring 上下文）。
 * 覆盖规范 §三 security/ 包权益矩阵（HLD §B4 / LLD 用户与权限 §2）：
 * A13 PUT /strategies、A15 POST /adapters/{id}/enable 需 pro/premium/admin，
 * 未达门槛 → 403 FORBIDDEN；其余路径放行；未设安全上下文 → fail-closed 401。
 */
class PermissionInterceptorTest {

    private PermissionInterceptor interceptor;

    @BeforeEach
    void setUp() {
        interceptor = new PermissionInterceptor();
    }

    @AfterEach
    void tearDown() {
        SecurityContext.clear();
    }

    private void asRole(String role) {
        SecurityContext.set(new UserContext("u1", role, role));
    }

    private MockHttpServletRequest req(String servletPath) {
        MockHttpServletRequest r = new MockHttpServletRequest();
        r.setServletPath(servletPath);
        return r;
    }

    // —— A13 PUT /strategies ——
    @Test
    void A13_strategies_free角色_抛403() {
        asRole("free");
        AuthException ex = assertThrows(AuthException.class,
                () -> interceptor.preHandle(req("/api/v1/strategies"), null, null));
        assertEquals("FORBIDDEN", ex.code);
        assertEquals(403, ex.httpStatus);
    }

    @Test
    void A13_strategies_pro角色_放行() throws Exception {
        asRole("pro");
        assertTrue(interceptor.preHandle(req("/api/v1/strategies"), null, null));
    }

    @Test
    void A13_strategies_premium角色_放行() throws Exception {
        asRole("premium");
        assertTrue(interceptor.preHandle(req("/api/v1/strategies"), null, null));
    }

    @Test
    void A13_strategies_admin角色_放行() throws Exception {
        asRole("admin");
        assertTrue(interceptor.preHandle(req("/api/v1/strategies"), null, null));
    }

    // —— A15 POST /adapters/{id}/enable ——
    @Test
    void A15_adapters_enable_free角色_抛403() {
        asRole("free");
        AuthException ex = assertThrows(AuthException.class,
                () -> interceptor.preHandle(req("/api/v1/adapters/123/enable"), null, null));
        assertEquals("FORBIDDEN", ex.code);
        assertEquals(403, ex.httpStatus);
    }

    @Test
    void A15_adapters_enable_premium角色_放行() throws Exception {
        asRole("premium");
        assertTrue(interceptor.preHandle(req("/api/v1/adapters/123/enable"), null, null));
    }

    // —— 非受保护路径 ——
    @Test
    void 非受保护路径_free角色_放行() throws Exception {
        asRole("free");
        assertTrue(interceptor.preHandle(req("/api/v1/jobs"), null, null));
    }

    // —— fail-closed：受保护路径但无安全上下文（过滤器未注入，理论上不应发生） ——
    @Test
    void 受保护路径_未设安全上下文_抛CREDENTIAL_MISSING() {
        // 不调用 asRole，SecurityContext 为空
        AuthException ex = assertThrows(AuthException.class,
                () -> interceptor.preHandle(req("/api/v1/strategies"), null, null));
        assertEquals("CREDENTIAL_MISSING", ex.code);
        assertEquals(401, ex.httpStatus);
    }
}
