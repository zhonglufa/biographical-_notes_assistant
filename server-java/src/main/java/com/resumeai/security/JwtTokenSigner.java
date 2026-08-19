package com.resumeai.security;

import io.jsonwebtoken.Jwts;

import java.security.PrivateKey;
import java.security.interfaces.RSAPrivateKey;
import java.util.Date;

/**
 * RS256 JWT 签发器（HLD §3.1 / ADR-017/018）。
 *
 * <p>取代 P0 的「mock token」：用 RsaKeyProvider 的私钥签出真实 RS256 令牌。
 * access / refresh 共用 claims 结构（sub / iss / plan / role / type），仅 TTL 与 type 不同；
 * 验签侧 JwtVerifier 读取 sub/role/plan，type 由刷新端点自行校验（见 UserServiceImpl.refresh）。</p>
 */
public class JwtTokenSigner {

    private final PrivateKey privateKey;
    private final String issuer;
    private final long accessTtlSeconds;
    private final long refreshTtlSeconds;

    public JwtTokenSigner(PrivateKey privateKey, String issuer,
                          long accessTtlSeconds, long refreshTtlSeconds) {
        this.privateKey = privateKey;
        this.issuer = issuer;
        this.accessTtlSeconds = accessTtlSeconds;
        this.refreshTtlSeconds = refreshTtlSeconds;
    }

    public String signAccess(String sub, String plan, String role) {
        return sign(sub, plan, role, "access", accessTtlSeconds);
    }

    public String signRefresh(String sub, String plan, String role) {
        return sign(sub, plan, role, "refresh", refreshTtlSeconds);
    }

    private String sign(String sub, String plan, String role, String type, long ttlSeconds) {
        long now = System.currentTimeMillis();
        return Jwts.builder()
                .issuer(issuer)
                .subject(sub)
                .claim("plan", plan)
                .claim("role", role)
                .claim("type", type)
                .issuedAt(new Date(now))
                .expiration(new Date(now + ttlSeconds * 1000L))
                .signWith((RSAPrivateKey) privateKey, Jwts.SIG.RS256)
                .compact();
    }
}
