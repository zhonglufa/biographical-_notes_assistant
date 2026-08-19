package com.resumeai.security;

import com.resumeai.config.JwtProperties;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 安全装配（规范 §三 security/ 包）。
 *
 * <p>关键：spring-boot-starter-security 在 classpath 上若不给 SecurityFilterChain，
 * Spring Boot 会自动给所有端点加默认 HTTP Basic 认证（全 401），原占位 extractUserId
 * 根本不会生效。本配置显式接管：关闭 CSRF/表单/HTTP Basic，全部 permitAll，
 * 由 JwtAuthFilter + PermissionInterceptor 真正执行 RS256 验签与权益矩阵判定。</p>
 */
@Configuration
@EnableConfigurationProperties(JwtProperties.class)
public class SecurityConfig {

    @Value("${resumeai.jwt.private-key:}")
    private String privateKeyPem;

    @Bean
    public RsaKeyProvider rsaKeyProvider(JwtProperties props) {
        return new RsaKeyProvider(props.publicKey(), privateKeyPem);
    }

    @Bean
    public JwtVerifier jwtVerifier(RsaKeyProvider keyProvider, JwtProperties props) {
        return new JwtVerifier(keyProvider.getPublicKey(), props.issuer());
    }

    @Bean
    public JwtTokenSigner jwtTokenSigner(RsaKeyProvider keyProvider, JwtProperties props) {
        return new JwtTokenSigner(keyProvider.getPrivateKey(),
                props.issuer(), props.accessTtlSeconds(), props.refreshTtlSeconds());
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http, JwtVerifier verifier) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .formLogin(AbstractHttpConfigurer::disable)
                .httpBasic(AbstractHttpConfigurer::disable)
                .authorizeHttpRequests(auth -> auth.anyRequest().permitAll())
                .addFilterBefore(new JwtAuthFilter(verifier), UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    @Bean
    public WebMvcConfigurer authInterceptors() {
        return new WebMvcConfigurer() {
            @Override
            public void addInterceptors(InterceptorRegistry registry) {
                registry.addInterceptor(new PermissionInterceptor())
                        .addPathPatterns("/api/v1/**");
            }
        };
    }
}
