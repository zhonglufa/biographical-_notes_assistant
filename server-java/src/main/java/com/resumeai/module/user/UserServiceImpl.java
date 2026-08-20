package com.resumeai.module.user;

import com.resumeai.common.BizException;
import com.resumeai.module.user.dto.*;
import com.resumeai.security.JwtTokenSigner;
import com.resumeai.security.JwtVerifier;
import com.resumeai.security.UserContext;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 用户与权限服务实现（A01/A02/A03）。
 *
 * <p>2026-08-19 收尾：将 P0 的「mock token」替换为真实 RS256 签发（ADR-017/018）。
 * 登录/刷新由 {@link JwtTokenSigner} 用 RsaKeyProvider 私钥签出 access/refresh JWT，
 * 验签经已有的 fail-closed {@link JwtVerifier}（JwtAuthFilter 在请求入口完成）。</p>
 *
 * <p>⚠️ 诚实偏差 B-1（MVP 限制，非生产级认证）：本实现仅做「非空 account/credential → 签发」，
 * 未接 {@code t_user} 持久层做密码哈希/注册流程。完整用户认证是独立子域且牵涉 PIPL（D 阶段已跳过），
 * 列为待办；生产接入时应在 {@code login} 内对凭据做哈希比对，而非无条件签发。</p>
 */
@Service
public class UserServiceImpl implements UserService {

    private final JwtTokenSigner signer;
    private final JwtVerifier verifier;

    public UserServiceImpl(JwtTokenSigner signer, JwtVerifier verifier) {
        this.signer = signer;
        this.verifier = verifier;
    }

    @Override
    public LoginResponse login(LoginRequest req) {
        if (req.account() == null || req.credential() == null
                || req.account().isBlank() || req.credential().isBlank()) {
            throw new BizException(400, "account and credential required");
        }
        // B-1：MVP 凭据校验（见类注释）。生产应改为对 t_user 做密码哈希比对。
        String sub = req.account();
        String access = signer.signAccess(sub, "free", "user");
        String refresh = signer.signRefresh(sub, "free", "user");
        return new LoginResponse(access, refresh, "free", List.of("jobs:view"));
    }

    @Override
    public LoginResponse refresh(RefreshRequest req) {
        if (req.refreshToken() == null || req.refreshToken().isBlank()) {
            throw new BizException(400, "refreshToken required");
        }
        // 刷新端点自身验签 refresh JWT（/auth/refresh 在过滤器跳过清单内，不前置验签）
        UserContext ctx = verifier.verify("Bearer " + req.refreshToken());
        String sub = ctx.userId();
        String access = signer.signAccess(sub, "free", "user");
        String refresh = signer.signRefresh(sub, "free", "user");
        return new LoginResponse(access, refresh, "free", List.of("jobs:view"));
    }

    @Override
    public UserMeResponse me(String userId) {
        // userId 已由 JwtAuthFilter 验签得到（SecurityContext.currentUserId），此处不再重复验签
        return new UserMeResponse(0L, userId, null, "free", List.of("jobs:view"));
    }

    @Override
    public PermissionsResponse permissions(String userId) {
        return new PermissionsResponse(List.of("jobs:view"));
    }
}
