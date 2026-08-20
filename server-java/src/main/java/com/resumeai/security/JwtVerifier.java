package com.resumeai.security;

import com.resumeai.config.JwtProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.JwtParser;
import io.jsonwebtoken.JwtParserBuilder;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.SignatureException;

import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

/**
 * RS256 JWT 验签器（HLD §3.1 / ADR-017/018）。
 * 仅用公钥验签（私钥存 KMS/配置中心，不落库、不进本类）；公钥来自 RsaKeyProvider（运行时）
 * 或 JwtProperties.publicKey(PEM，测试兼容)。
 * fail-closed：公钥缺失 / 令牌缺失 / 验签失败 / 过期 → 抛 AuthException，绝不放行。
 */
public class JwtVerifier {

    private final PublicKey publicKey;
    private final String issuer;

    /**
     * 运行时构造：由 SecurityConfig 注入 RsaKeyProvider 的公钥与 issuer。
     */
    public JwtVerifier(PublicKey publicKey, String issuer) {
        this.publicKey = publicKey;
        this.issuer = issuer;
    }

    /**
     * 测试/遗留构造：从 JwtProperties 的 PEM 公钥解析（兼容既有单测，零改动）。
     */
    public JwtVerifier(JwtProperties props) {
        this.issuer = props.issuer();
        this.publicKey = parsePublicKey(props.publicKey());
    }

    /**
     * 校验 Bearer 令牌，返回解析出的用户上下文。任何失效都抛 AuthException（fail-closed）。
     */
    public UserContext verify(String bearer) {
        if (bearer == null || bearer.isBlank()) {
            throw AuthException.credentialMissing();
        }
        String token = bearer.startsWith("Bearer ") ? bearer.substring(7).trim() : bearer.trim();
        if (token.isBlank()) {
            throw AuthException.credentialMissing();
        }
        // fail-closed：公钥未配置（含临时密钥未生成场景）→ 拒绝一切
        if (publicKey == null) {
            throw AuthException.credentialMissing();
        }

        try {
            JwtParserBuilder builder = Jwts.parser().verifyWith((RSAPublicKey) publicKey);
            if (issuer != null && !issuer.isBlank()) {
                builder.requireIssuer(issuer);
            }
            JwtParser parser = builder.build();
            Claims claims = parser.parseSignedClaims(token).getPayload();

            String sub = claims.getSubject();
            if (sub == null || sub.isBlank()) {
                throw AuthException.unauthorized();
            }
            String role = claims.get("role", String.class);
            String plan = claims.get("plan", String.class);
            return new UserContext(sub, role, plan);
        } catch (ExpiredJwtException e) {
            throw AuthException.tokenExpired();
        } catch (SignatureException | MalformedJwtException | UnsupportedJwtException
                 | IllegalArgumentException e) {
            throw AuthException.unauthorized();
        } catch (JwtException e) {
            throw AuthException.unauthorized();
        }
    }

    private static RSAPublicKey parsePublicKey(String pem) {
        if (pem == null || pem.isBlank()) {
            return null;
        }
        try {
            String b64 = pem
                    .replaceAll("-----BEGIN PUBLIC KEY-----", "")
                    .replaceAll("-----END PUBLIC KEY-----", "")
                    .replaceAll("\\s+", "");
            byte[] der = Base64.getDecoder().decode(b64);
            KeyFactory kf = KeyFactory.getInstance("RSA");
            return (RSAPublicKey) kf.generatePublic(new X509EncodedKeySpec(der));
        } catch (Exception e) {
            return null;
        }
    }
}
