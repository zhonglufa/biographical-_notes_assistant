package com.resumeai.module.payment.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.payment.entity.MemberOrder;

public interface MemberOrderRepository extends BaseMapper<MemberOrder> {


    default Optional<MemberOrder> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default MemberOrder save(MemberOrder e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<MemberOrder> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default Optional<MemberOrder> findByOrderNo(String orderNo) {
        return Optional.ofNullable(selectOne(new QueryWrapper<MemberOrder>().eq("order_no", orderNo)));
    }

}
