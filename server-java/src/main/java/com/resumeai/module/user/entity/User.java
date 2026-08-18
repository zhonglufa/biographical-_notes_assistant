package com.resumeai.module.user.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 用户实体（t_user）。plan ∈ {free, pro, premium, admin}（HLD §3.1 权益矩阵）。
 * 字段与 LLD-用户与权限模块-模块设计.md v1.0 一致。
 */
@TableName("t_user")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class User {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("email")
    private String email;

    @TableField("phone")
    private String phone;
    @TableField("password_hash")
    private String passwordHash;
    @TableField("plan")
    private String plan;
}
