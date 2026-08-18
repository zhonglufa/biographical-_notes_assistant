package com.resumeai.module.user;

import com.resumeai.module.user.dto.*;

/**
 * 用户与权限服务接口（A01/A02/A03）。
 */
public interface UserService {
    LoginResponse login(LoginRequest req);

    LoginResponse refresh(RefreshRequest req);

    UserMeResponse me(String token);

    PermissionsResponse permissions(String token);
}
