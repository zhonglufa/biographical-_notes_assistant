package com.resumeai.security;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/**
 * 权益矩阵拦截器（规范 §三 security/ 包；HLD §B4 / LLD 用户与权限 §2）。
 * 在 MVC 内执行，异常由 GlobalExceptionHandler 捕获转译为 ErrorEnvelope。
 *
 * <p>角色门槛派生自 design/contracts/external-api.registry.json 的 auth 列：
 * - Bearer（多数端点）：仅要求已认证（过滤器已保证），无额外角色门槛；
 * - Bearer+pro（A13 PUT /strategies、A15 POST /adapters/{id}/enable）：需 pro/premium/admin；
 * - Bearer+role（A09 POST /applications/batch）：仅要求已认证，日限额在业务层按角色强制；
 * - Bearer(query)（A23 WS）：过滤器已处理，此处无门槛。
 * fail-closed：未达角色门槛 → 403 FORBIDDEN。</p>
 */
public class PermissionInterceptor implements HandlerInterceptor {

    private static final AntPathMatcher MATCHER = new AntPathMatcher();

    /** 路径(精确或 Ant 通配) → 允许的最低套餐角色集合。 */
    private static final Map<String, Set<String>> PRO_REQUIRED = new LinkedHashMap<>();

    static {
        Set<String> proPlus = Set.of("pro", "premium", "admin");
        PRO_REQUIRED.put("/api/v1/strategies", proPlus);          // A13 PUT
        PRO_REQUIRED.put("/api/v1/adapters/*/enable", proPlus);   // A15
    }

    @Override
    public boolean preHandle(HttpServletRequest request,
                             HttpServletResponse response,
                             Object handler) {
        String path = request.getServletPath();
        for (Map.Entry<String, Set<String>> e : PRO_REQUIRED.entrySet()) {
            if (MATCHER.match(e.getKey(), path)) {
                UserContext ctx = SecurityContext.current(); // 已认证（过滤器保证）
                if (!e.getValue().contains(ctx.role())) {
                    throw AuthException.forbidden();
                }
                return true;
            }
        }
        return true;
    }
}
