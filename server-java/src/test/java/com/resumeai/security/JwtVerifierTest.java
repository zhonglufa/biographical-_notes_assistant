package com.resumeai.security;

import com.resumeai.config.JwtProperties;
import io.jsonwebtoken.JwtBuilder;
import io.jsonwebtoken.Jwts;
import org.junit.jupiter.api.Test;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.Base64;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

/**
 * JwtVerifier 单元测试（纯函数，不引 Spring 上下文）。
 * 覆盖 HLD §3.1 / ADR-017/018 的 fail-closed 语义：
 * 验签成功 / 签名错误 / 过期 / 缺凭证(null·空白·无公钥) / 缺 subject / issuer 不匹配。
 */
class JwtVerifierTest {

    private static final String ISSUER = "resumeai";

    private KeyPair rsa() throws Exception {
        KeyPairGenerator g = KeyPairGenerator.getInstance("RSA");
        g.initialize(2048);
        return g.generateKeyPair();
    }

    private String publicKeyPem(RSAPublicKey pub) {
        String b64 = Base64.getEncoder().encodeToString(pub.getEncoded());
        return "-----BEGIN PUBLIC KEY-----\n" + b64 + "\n-----END PUBLIC KEY-----\n";
    }

    private String sign(RSAPrivateKey priv, String sub, String role, String plan,
                         String issuer, Date exp) {
        JwtBuilder b = Jwts.builder()
                .subject(sub)
                .claim("role", role)
                .claim("plan", plan)
                .issuer(issuer)
                .expiration(exp);
        return b.signWith(priv, Jwts.SIG.RS256).compact();
    }

    @Test
    void 验签成功_返回用户上下文() throws Exception {
        KeyPair kp = rsa();
        JwtProperties props = new JwtProperties(ISSUER,
                publicKeyPem((RSAPublicKey) kp.getPublic()), 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        Date exp = new Date(System.currentTimeMillis() + 3_600_000L);
        String token = sign((RSAPrivateKey) kp.getPrivate(),
                "user-123", "pro", "pro", ISSUER, exp);

        UserContext ctx = verifier.verify("Bearer " + token);

        assertEquals("user-123", ctx.userId());
        assertEquals("pro", ctx.role());
        assertEquals("pro", ctx.plan());
    }

    @Test
    void 验签成功_无Bearer前缀_亦可() throws Exception {
        KeyPair kp = rsa();
        JwtProperties props = new JwtProperties(ISSUER,
                publicKeyPem((RSAPublicKey) kp.getPublic()), 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        Date exp = new Date(System.currentTimeMillis() + 3_600_000L);
        String token = sign((RSAPrivateKey) kp.getPrivate(),
                "u9", "admin", "admin", ISSUER, exp);

        UserContext ctx = verifier.verify(token); // 无 Bearer 前缀
        assertEquals("u9", ctx.userId());
    }

    @Test
    void 签名错误_抛UNAUTHORIZED() throws Exception {
        KeyPair good = rsa();
        KeyPair evil = rsa(); // 不同私钥 → 验签必败
        JwtProperties props = new JwtProperties(ISSUER,
                publicKeyPem((RSAPublicKey) good.getPublic()), 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        Date exp = new Date(System.currentTimeMillis() + 3_600_000L);
        String token = sign((RSAPrivateKey) evil.getPrivate(),
                "user-123", "pro", "pro", ISSUER, exp);

        AuthException ex = assertThrows(AuthException.class,
                () -> verifier.verify("Bearer " + token));
        assertEquals("UNAUTHORIZED", ex.code);
        assertEquals(401, ex.httpStatus);
    }

    @Test
    void 令牌过期_抛TOKEN_EXPIRED() throws Exception {
        KeyPair kp = rsa();
        JwtProperties props = new JwtProperties(ISSUER,
                publicKeyPem((RSAPublicKey) kp.getPublic()), 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        Date past = new Date(System.currentTimeMillis() - 10_000L);
        String token = sign((RSAPrivateKey) kp.getPrivate(),
                "user-123", "pro", "pro", ISSUER, past);

        AuthException ex = assertThrows(AuthException.class,
                () -> verifier.verify("Bearer " + token));
        assertEquals("TOKEN_EXPIRED", ex.code);
        assertEquals(401, ex.httpStatus);
    }

    @Test
    void 缺少凭证_null_抛CREDENTIAL_MISSING() {
        JwtProperties props = new JwtProperties(ISSUER, "dummy-pub", 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        AuthException ex = assertThrows(AuthException.class,
                () -> verifier.verify(null));
        assertEquals("CREDENTIAL_MISSING", ex.code);
        assertEquals(401, ex.httpStatus);
    }

    @Test
    void 缺少凭证_空白与纯Bearer_抛CREDENTIAL_MISSING() {
        JwtProperties props = new JwtProperties(ISSUER, "dummy-pub", 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        assertThrows(AuthException.class, () -> verifier.verify(""));
        assertThrows(AuthException.class, () -> verifier.verify("Bearer   "));
        assertThrows(AuthException.class, () -> verifier.verify("   "));
    }

    @Test
    void 未配置公钥_抛CREDENTIAL_MISSING() throws Exception {
        // fail-closed：生产必须显式注入公钥，无开发后门
        JwtProperties props = new JwtProperties(ISSUER, null, 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        KeyPair kp = rsa();
        Date exp = new Date(System.currentTimeMillis() + 3_600_000L);
        String token = sign((RSAPrivateKey) kp.getPrivate(),
                "u", "pro", "pro", ISSUER, exp);

        AuthException ex = assertThrows(AuthException.class,
                () -> verifier.verify("Bearer " + token));
        assertEquals("CREDENTIAL_MISSING", ex.code);
    }

    @Test
    void 令牌缺subject_抛UNAUTHORIZED() throws Exception {
        KeyPair kp = rsa();
        JwtProperties props = new JwtProperties(ISSUER,
                publicKeyPem((RSAPublicKey) kp.getPublic()), 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        String token = Jwts.builder()
                .claim("role", "pro")
                .claim("plan", "pro")
                .issuer(ISSUER)
                .expiration(new Date(System.currentTimeMillis() + 3_600_000L))
                .signWith((RSAPrivateKey) kp.getPrivate(), Jwts.SIG.RS256)
                .compact();

        AuthException ex = assertThrows(AuthException.class,
                () -> verifier.verify("Bearer " + token));
        assertEquals("UNAUTHORIZED", ex.code);
    }

    @Test
    void issuer不匹配_抛UNAUTHORIZED() throws Exception {
        KeyPair kp = rsa();
        JwtProperties props = new JwtProperties("resumeai",
                publicKeyPem((RSAPublicKey) kp.getPublic()), 3600, 86400);
        JwtVerifier verifier = new JwtVerifier(props);
        Date exp = new Date(System.currentTimeMillis() + 3_600_000L);
        // 用错误 issuer 签发
        String token = sign((RSAPrivateKey) kp.getPrivate(),
                "u", "pro", "pro", "wrong-issuer", exp);

        AuthException ex = assertThrows(AuthException.class,
                () -> verifier.verify("Bearer " + token));
        assertEquals("UNAUTHORIZED", ex.code);
    }
}
