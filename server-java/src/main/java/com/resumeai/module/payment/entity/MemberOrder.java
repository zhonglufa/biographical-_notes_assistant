package com.resumeai.module.payment.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 会员订单（对齐 DB member_order，R-04 资损级资金链路权威）。
 * 状态机：pending→paid→activated→expired→refunded，closed 终态（payment LLD §1）。
 * userId 沿用 P0/P1 的 String(36) 约定（与 LLD BIGINT 偏差已登记）。
 */
@Entity
@Table(name = "member_order")
@Getter
@Setter
@NoArgsConstructor
public class MemberOrder {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String orderNo;

    @Column(nullable = false)
    private String userId;

    @Column(nullable = false)
    private String plan;

    private int months;

    @Column(nullable = false)
    private int amount; // 整数分

    @Column(nullable = false)
    private String status = "pending";

    private String couponCode;

    @Column(name = "expire_at")
    private Long expireAt;

    @Column(name = "paid_at")
    private Long paidAt;

    @Column(name = "created_at")
    private Long createdAt = System.currentTimeMillis();
}
