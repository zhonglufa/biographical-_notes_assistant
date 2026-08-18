package com.resumeai.module.user;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.user.dto.*;
import com.resumeai.security.SecurityContext;
import org.springframework.web.bind.annotation.*;

/**
 * 用户与权限 REST 控制器（A01/A02/A03）。
 * 路径对齐 design/contracts/implementation-index.md。
 *
 * <p>鉴权：/auth/login、/auth/refresh 免 JWT（登录前无令牌，由 JwtAuthFilter 跳过）；
 * /auth/users/me、/auth/users/me/permissions（A03）需有效 JWT，userId 由 SecurityContext 提供。</p>
 */
@RestController
@RequestMapping("/auth")
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@RequestBody LoginRequest req) {
        return ApiResponse.ok(userService.login(req));
    }

    @PostMapping("/refresh")
    public ApiResponse<LoginResponse> refresh(@RequestBody RefreshRequest req) {
        return ApiResponse.ok(userService.refresh(req));
    }

    @GetMapping("/users/me")
    public ApiResponse<UserMeResponse> me() {
        return ApiResponse.ok(userService.me(SecurityContext.currentUserId()));
    }

    @GetMapping("/users/me/permissions")
    public ApiResponse<PermissionsResponse> permissions() {
        return ApiResponse.ok(userService.permissions(SecurityContext.currentUserId()));
    }
}
