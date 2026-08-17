package com.resumeai.module.user;

import com.resumeai.common.ApiResponse;
import com.resumeai.module.user.dto.*;
import org.springframework.web.bind.annotation.*;

/**
 * 用户与权限 REST 控制器（A01/A02/A03）。
 * 路径对齐 design/contracts/implementation-index.md。
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
    public ApiResponse<UserMeResponse> me(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(userService.me(strip(auth)));
    }

    @GetMapping("/users/me/permissions")
    public ApiResponse<PermissionsResponse> permissions(@RequestHeader("Authorization") String auth) {
        return ApiResponse.ok(userService.permissions(strip(auth)));
    }

    private String strip(String auth) {
        if (auth != null && auth.startsWith("Bearer ")) {
            return auth.substring(7);
        }
        return auth;
    }
}
