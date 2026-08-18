package com.resumeai.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Set;
import java.util.UUID;

/**
 * RS256 JWT 认证过滤器（规范 §三 security/ 包）。
 * 在 SecurityFilterChain 中置于 UsernamePasswordAuthenticationFilter 之前。
 *
 * <p>关键点：过滤器阶段抛出的异常 {@link GlobalExceptionHandler}（@RestControllerAdvice）捕获不到，
 * 会漏给容器返回 HTML 500；因此本过滤器在内部捕获 AuthException 并自行写入
 * {@link com.resumeai.common.ErrorEnvelope} JSON + 正确 HTTP 状态。</p>
 *
 * <p>跳过清单（不要求 JWT）：登录/刷新（/auth/login、/auth/refresh）、存活探针（/healthz）、
 * 支付渠道回调（/api/v1/payments/callback，走渠道非对称签名而非 Bearer）。
 * A23 通知 WS 令牌经 query 传递（auth=Bearer(query)），从 ?token= 读取。</p>
 */
public class JwtAuthFilter extends OncePerRequestFilter {

    private final JwtVerifier verifier;

    private static final Set<String> SKIP = Set.of(
            "/auth/login",
            "/auth/refresh",
            "/healthz",
            "/api/v1/payments/callback"
    );

    public JwtAuthFilter(JwtVerifier verifier) {
        this.verifier = verifier;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String p = request.getServletPath();
        if (SKIP.contains(p)) {
            return true;
        }
        return p.startsWith("/actuator/");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                     HttpServletResponse response,
                                     FilterChain chain) throws ServletException, IOException {
        String path = request.getServletPath();
        // A23 WebSocket：令牌在 query（Bearer(query)），其余从 Authorization 头取
        String bearer = path.equals("/api/v1/notifications/ws")
                ? request.getParameter("token")
                : request.getHeader("Authorization");
        try {
            UserContext ctx = verifier.verify(bearer);
            SecurityContext.set(ctx);
            chain.doFilter(request, response);
        } catch (AuthException ae) {
            writeError(response, ae);
        } finally {
            SecurityContext.clear();
        }
    }

    private void writeError(HttpServletResponse response, AuthException ae) throws IOException {
        response.setStatus(ae.httpStatus);
        response.setContentType("application/json;charset=UTF-8");
        String traceId = UUID.randomUUID().toString();
        String json = "{\"code\":\"" + ae.code + "\",\"message\":\"" + escape(ae.getMessage())
                + "\",\"traceId\":\"" + traceId + "\",\"retryable\":" + ae.retryable
                + ",\"user_action\":\"" + escape(ae.userAction) + "\"}";
        response.getWriter().write(json);
    }

    private static String escape(String s) {
        if (s == null) {
            return "";
        }
        return s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    }
}
