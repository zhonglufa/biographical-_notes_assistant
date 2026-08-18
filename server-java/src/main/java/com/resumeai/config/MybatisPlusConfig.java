package com.resumeai.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * MyBatis-Plus 配置（ORM 迁移 ADR-002：JPA → MyBatis-Plus）。
 *
 * <p>@MapperScan 仅扫描各模块的 repository 包（com.resumeai.module.*.repository），
 * 不扫描 service / client 等其它接口，避免 MyBatis 把非 Mapper 接口误注册为 MapperFactoryBean。</p>
 *
 * <p>分页拦截器使用 DbType.MYSQL；测试环境 H2 以 MODE=MySQL 运行，LIMIT/OFFSET 分页方言与 MySQL 一致，可共用。</p>
 */
@Configuration
@MapperScan("com.resumeai.module.*.repository")
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
