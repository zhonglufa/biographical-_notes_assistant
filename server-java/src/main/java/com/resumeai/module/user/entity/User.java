package com.resumeai.module.user.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 用户实体（t_user）。plan ∈ {free, pro, premium, admin}（HLD §3.1 权益矩阵）。
 * 字段与 LLD-用户与权限模块-模块设计.md v1.0 一致。
 */
@Entity
@Table(name = "t_user")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true)
    private String email;

    private String phone;
    private String passwordHash;
    private String plan;
}
