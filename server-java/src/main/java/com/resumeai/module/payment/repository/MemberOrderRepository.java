package com.resumeai.module.payment.repository;

import com.resumeai.module.payment.entity.MemberOrder;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface MemberOrderRepository extends JpaRepository<MemberOrder, Long> {
    Optional<MemberOrder> findByOrderNo(String orderNo);
}
