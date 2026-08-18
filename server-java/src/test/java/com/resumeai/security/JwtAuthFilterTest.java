package com.resumeai.security;

import com.resumeai.config.JwtProperties;
import io.jsonwebtoken.Jwts;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.Base64;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

/**
 * JwtAuthFilter 单元测试（HTTP 边界过滤器，纯函数，不引 Spring 上下文）。
 *
 * <p>这是认证链最外层的 fail-closed 边界：过滤器阶段抛的异常 GlobalExceptionHandler
 * 捕获不到，必须自写 ErrorEnvelope JSON。本测试覆盖：
 * <ul>
 *   <li>跳过清单（login/refresh/healthz/payments-callback/actuator）→ 直接放行、不验签；</li>
 *   <li>合法 Bearer（含无前缀裸 token）→ 设 SecurityContext、放行、finally 清理；</li>
 *   <li>WS 路径 /api/v1/notifications/ws → 令牌从 ?token= query 取，不从 Authorization 头；</li>
 *   <li>缺失/空白令牌 → 401 CREDENTIAL_MISSING，链不继续；</li>
 *   <li>非法签名 → 401 UNAUTHORIZED；过期 → 401 TOKEN_EXPIRED；</li>
 *   <li>认证失败后：SecurityContext 必清理 + 响应写入 ErrorEnvelope JSON。</li>
 * </ul>
 *
 * <p>沿用本包既有风格：RSA 密钥测试内现造、jwt 现签；请求/响应用 spring-test 的
 * MockHttpServletRequest/Response；FilterChain 用手写录制实现（不引 Mockito）。
 */
class JwtAuthFilterTest {

    private static final String ISSUER = "resumeai";

    private KeyPair kp;
    private JwtVerifier verifier;
    private JwtAuthFilter filter;
    private String validToken;
    private String expiredToken;
    private String evilSignedToken;

    @BeforeEach
    void setUp() throws Exception {
        KeyPairGenerator g = KeyPairGenerator.getInstance("RSA");
        g.initialize(2048);
        kp = g.generateKeyPair();

        String pem = "-----BEGIN PUBLIC KEY-----\n"
                + Base64.getEncoder().encodeToString(kp.getPublic().getEncoded())
                + "\n-----END PUBLIC KEY-----\n";
        JwtProperties props = new JwtProperties(ISSUER, pem, 3600, 86400);
        verifier = new JwtVerifier(props);
        filter = new JwtAuthFilter(verifier);

        Date future = new Date(System.currentTimeMillis() + 3_600_000L);
        Date past = new Date(System.currentTimeMillis() - 10_000L);

        validToken = sign("user-42", "pro", "pro", ISSUER, future);
        expiredToken = sign("user-42", "pro", "pro", ISSUER, past);

        // 用另一对密钥签名 → 验签必败（UNAUTHORIZED）
        KeyPair evil = KeyPairGenerator.getInstance("RSA").generateKeyPair();
        evilSignedToken = signWith((RSAPrivateKey) evil.getPrivate(), "user-42", "pro", "pro", ISSUER, future);
    }

    @AfterEach
    void tearDown() {
        SecurityContext.clear();
    }

    // —— 手写 FilterChain：录制是否放行 + 放行瞬间的安全上下文 ——
    static class RecordingChain implements FilterChain {
        boolean called = false;
        String capturedUserIdDuringChain;

        @Override
        public void doFilter(ServletRequest request, ServletResponse response) {
            called = true;
            if (SecurityContext.isAuthenticated()) {
                capturedUserIdDuringChain = SecurityContext.currentUserId();
            }
        }
    }

    private MockHttpServletRequest req(String servletPath) {
        MockHttpServletRequest r = new MockHttpServletRequest();
        r.setServletPath(servletPath);
        return r;
    }

    private String sign(String sub, String role, String plan, String issuer, Date exp) throws Exception {
        return signWith((RSAPrivateKey) kp.getPrivate(), sub, role, plan, issuer, exp);
    }

    private String signWith(RSAPrivateKey priv, String sub, String role, String plan,
                             String issuer, Date exp) {
        return Jwts.builder()
                .subject(sub)
                .claim("role", role)
                .claim("plan", plan)
                .issuer(issuer)
                .expiration(exp)
                .signWith(priv, Jwts.SIG.RS256)
                .compact();
    }

    // —— 成功路径 ——

    @Test
    void 合法Bearer_设置上下文并放行() throws Exception {
        MockHttpServletRequest request = req("/api/v1/jobs");
        request.addHeader("Authorization", "Bearer " + validToken);
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertTrue(chain.called, "合法令牌应放行过滤器链");
        assertEquals("user-42", chain.capturedUserIdDuringChain, "放行瞬间应已注入正确的用户上下文");
        assertEquals(200, response.getStatus(), "成功路径不应改写 HTTP 状态");
        assertFalse(SecurityContext.isAuthenticated(), "finally 必须清理线程级安全上下文，避免串号");
    }

    @Test
    void 无Bearer前缀的裸token_仍可验签放行() throws Exception {
        MockHttpServletRequest request = req("/api/v1/jobs");
        request.addHeader("Authorization", validToken); // 无 "Bearer " 前缀
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertTrue(chain.called);
        assertEquals("user-42", chain.capturedUserIdDuringChain);
    }

    // —— 跳过清单：直接放行，不调 verifier ——

    @Test
    void 跳过清单路径_不验签直接放行() throws Exception {
        String[] skipPaths = {
                "/auth/login", "/auth/refresh", "/healthz",
                "/api/v1/payments/callback", "/actuator/health"
        };
        for (String path : skipPaths) {
            MockHttpServletRequest request = req(path);
            // 故意不带任何令牌，若走验签必炸；能放行说明被跳过
            MockHttpServletResponse response = new MockHttpServletResponse();
            RecordingChain chain = new RecordingChain();

            filter.doFilter(request, response, chain);

            assertTrue(chain.called, path + " 应在跳过清单中直接放行");
        }
    }

    // —— WS 路径：令牌来自 query 参数 ——

    @Test
    void WS路径_从query参数取token_放行() throws Exception {
        MockHttpServletRequest request = req("/api/v1/notifications/ws");
        request.addParameter("token", validToken); // 不在 Authorization 头
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertTrue(chain.called);
        assertEquals("user-42", chain.capturedUserIdDuringChain);
    }

    @Test
    void WS路径_缺token参数_401() throws Exception {
        MockHttpServletRequest request = req("/api/v1/notifications/ws");
        // 既不带 Authorization 头也不带 ?token=
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertFalse(chain.called, "缺令牌不应放行");
        assertEquals(401, response.getStatus());
        assertFalse(SecurityContext.isAuthenticated());
    }

    // —— 失败路径：认证失败 → 401 + 不链续 + 清理 + 写 JSON ——

    @Test
    void 缺失Authorization头_401_CREDENTIAL_MISSING() throws Exception {
        MockHttpServletRequest request = req("/api/v1/jobs");
        // 不设任何 Authorization
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertFalse(chain.called, "缺凭证不应放行过滤器链");
        assertEquals(401, response.getStatus());
        assertTrue(response.getContentType().contains("application/json"), "应返回 JSON 错误包络");
        String body = response.getContentAsString();
        assertTrue(body.contains("\"code\":\"CREDENTIAL_MISSING\""), "错误码应为 CREDENTIAL_MISSING，实际: " + body);
        assertFalse(SecurityContext.isAuthenticated());
    }

    @Test
    void 空白Bearer_401() throws Exception {
        MockHttpServletRequest request = req("/api/v1/jobs");
        request.addHeader("Authorization", "Bearer   "); // 只有前缀无实质
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertFalse(chain.called);
        assertEquals(401, response.getStatus());
        assertTrue(response.getContentAsString().contains("CREDENTIAL_MISSING"));
    }

    @Test
    void 非法签名令牌_401_UNAUTHORIZED() throws Exception {
        MockHttpServletRequest request = req("/api/v1/jobs");
        request.addHeader("Authorization", "Bearer " + evilSignedToken);
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertFalse(chain.called);
        assertEquals(401, response.getStatus());
        assertTrue(response.getContentAsString().contains("\"code\":\"UNAUTHORIZED\""));
        assertFalse(SecurityContext.isAuthenticated());
    }

    @Test
    void 过期令牌_401_TOKEN_EXPIRED() throws Exception {
        MockHttpServletRequest request = req("/api/v1/jobs");
        request.addHeader("Authorization", "Bearer " + expiredToken);
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        assertFalse(chain.called);
        assertEquals(401, response.getStatus());
        assertTrue(response.getContentAsString().contains("\"code\":\"TOKEN_EXPIRED\""));
    }

    @Test
    void 认证失败后_响应含traceId与retryable字段() throws Exception {
        MockHttpServletRequest request = req("/api/v1/jobs");
        MockHttpServletResponse response = new MockHttpServletResponse();
        RecordingChain chain = new RecordingChain();

        filter.doFilter(request, response, chain);

        String body = response.getContentAsString();
        assertTrue(body.contains("\"traceId\""), "ErrorEnvelope 应含 traceId 便于排障");
        assertTrue(body.contains("\"retryable\":false"), "鉴权失败不可重试");
    }
}
