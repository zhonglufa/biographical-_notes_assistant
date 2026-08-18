package com.resumeai.module.payment.entity;
import com.baomidou.mybatisplus.annotation.*;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 会员订单（对齐 DB member_order，R-04 资损级资金链路权威）。
 * 状态机：pending→paid→activated→expired→refunded，closed 终态（payment LLD §1）。
 * userId 沿用 P0/P1 的 String(36) 约定（与 LLD BIGINT 偏差已登记）。
 */
@TableName("member_order")
@Getter
@Setter
@NoArgsConstructor
public class MemberOrder {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("order_no")
    private String orderNo;

    @TableField("user_id")
    private String userId;

    @TableField("plan")
    private String plan;

    @TableField("months")
    private int months;

    @TableField("amount")
    private int amount; // 整数分

    @TableField("status")
    private String status= "pending";

    @TableField("coupon_code")
    private String couponCode;

    @TableField("expire_at")
    private Long expireAt;

    @TableField("paid_at")
    private Long paidAt;

    @TableField("created_at")
    private Long createdAt= System.currentTimeMillis();
}
