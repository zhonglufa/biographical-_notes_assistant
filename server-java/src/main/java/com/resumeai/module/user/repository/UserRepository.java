package com.resumeai.module.user.repository;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.io.Serializable;
import java.util.List;
import java.util.Optional;

import com.resumeai.module.user.entity.User;
/**
 * 用户仓储（仅 Java 直连业务库，ADR-002 存储解耦）。
 */
public interface UserRepository extends BaseMapper<User> {


    default Optional<User> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }
    default User save(User e) { if (updateById(e) == 0) insert(e); return e; }
    default boolean existsById(Serializable id) { return selectById(id) != null; }
    default List<User> findAll() { return selectList(null); }
    default long count() { return selectCount(null); }
    default User findByEmail(String email) {
        return selectOne(new QueryWrapper<User>().eq("email", email));
    }

}
