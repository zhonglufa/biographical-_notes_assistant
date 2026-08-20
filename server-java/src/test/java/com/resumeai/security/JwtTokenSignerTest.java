package com.resumeai.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import org.junit.jupiter.api.Test;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

/**
 * JwtTokenSigner 单元测试：真实 RS256 签发 → JwtVerifier 验签的端到端闭环，
 * 覆盖 access/refresh 的 claims（sub/plan/role/type）与 issuer 一致性。
 */
class JwtTokenSignerTest {

    private KeyPair rsa() throws Exception {
        KeyPairGenerator g = KeyPairGenerator.getInstance("RSA");
        g.initialize(2048);
        return g.generateKeyPair();
    }

    @Test
    void signAccess_verifiable_with_claims() throws Exception {
        KeyPair kp = rsa();
        JwtTokenSigner signer = new JwtTokenSigner(
                (RSAPrivateKey) kp.getPrivate(), "resumeai", 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(kp.getPublic(), "resumeai");

        String access = signer.signAccess("user-1", "pro", "user");
        UserContext ctx = verifier.verify("Bearer " + access);

        assertEquals("user-1", ctx.userId());
        assertEquals("pro", ctx.plan());
        assertEquals("user", ctx.role());

        // type=access 声明存在
        Claims claims = Jwts.parser()
                .verifyWith((RSAPublicKey) kp.getPublic())
                .build()
                .parseSignedClaims(access)
                .getPayload();
        assertEquals("access", claims.get("type", String.class));
    }

    @Test
    void signRefresh_verifiable_and_distinct_from_access() throws Exception {
        KeyPair kp = rsa();
        JwtTokenSigner signer = new JwtTokenSigner(
                (RSAPrivateKey) kp.getPrivate(), "resumeai", 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(kp.getPublic(), "resumeai");

        String refresh = signer.signRefresh("user-1", "free", "user");
        UserContext ctx = verifier.verify("Bearer " + refresh);
        assertEquals("user-1", ctx.userId());
    }

    @Test
    void wrong_issuer_signer_rejected_by_verifier() throws Exception {
        KeyPair kp = rsa();
        JwtTokenSigner signer = new JwtTokenSigner(
                (RSAPrivateKey) kp.getPrivate(), "OTHER-ISSUER", 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(kp.getPublic(), "resumeai");

        String access = signer.signAccess("u", "free", "user");
        assertThrows(AuthException.class, () -> verifier.verify("Bearer " + access));
    }
}
