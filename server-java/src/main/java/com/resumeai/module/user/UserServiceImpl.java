package com.resumeai.module.user;

import com.resumeai.common.BizException;
import com.resumeai.module.user.dto.*;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 用户与权限服务实现（P0 骨架）。
 * <p>TODO(数据层批次): 当前为内存 mock，待接入 JPA {@code UserRepository} 与 RS256 签发（HLD §3.1 ADR-017/018）。
 * 仅用于验证模块结构、编译与契约对齐，不构成生产认证逻辑。</p>
 */
@Service
public class UserServiceImpl implements UserService {
    private final Map<String, String> tokens = new ConcurrentHashMap<>();

    @Override
    public LoginResponse login(LoginRequest req) {
        if (req.account() == null || req.credential() == null) {
            throw new BizException(400, "account and credential required");
        }
        String token = "mock-" + req.account();
        tokens.put(token, req.account());
        return new LoginResponse(token, token + "-rt", "free", List.of("jobs:view"));
    }

    @Override
    public LoginResponse refresh(RefreshRequest req) {
        if (req.refreshToken() == null) {
            throw new BizException(400, "refreshToken required");
        }
        return new LoginResponse(req.refreshToken().replace("-rt", ""), req.refreshToken(), "free", List.of("jobs:view"));
    }

    @Override
    public UserMeResponse me(String token) {
        String account = tokens.getOrDefault(token, "unknown");
        return new UserMeResponse(0L, account, null, "free", List.of("jobs:view"));
    }

    @Override
    public PermissionsResponse permissions(String token) {
        return new PermissionsResponse(List.of("jobs:view"));
    }
}
