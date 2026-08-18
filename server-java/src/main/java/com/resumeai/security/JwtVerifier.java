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
import org.springframework.stereotype.Component;

import java.security.KeyFactory;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

/**
 * RS256 JWT 验签器（HLD §3.1 / ADR-017/018）。
 * 仅用公钥验签（私钥存 KMS/配置中心，不落库、不进本类）；公钥来自 JwtProperties.publicKey(PEM)。
 * fail-closed：公钥未配置 / 令牌缺失 / 验签失败 / 过期 → 抛 AuthException，绝不放行。
 */
@Component
public class JwtVerifier {

    private final JwtProperties props;
    private volatile RSAPublicKey cachedKey;

    public JwtVerifier(JwtProperties props) {
        this.props = props;
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

        RSAPublicKey key = publicKey();
        try {
            JwtParserBuilder builder = Jwts.parser().verifyWith(key);
            if (props.issuer() != null && !props.issuer().isBlank()) {
                builder.requireIssuer(props.issuer());
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

    private RSAPublicKey publicKey() {
        RSAPublicKey k = cachedKey;
        if (k != null) {
            return k;
        }
        String pem = props.publicKey();
        if (pem == null || pem.isBlank()) {
            // 未配置公钥 → fail-closed：拒绝一切（生产必须显式注入公钥，无开发后门）
            throw AuthException.credentialMissing();
        }
        try {
            String b64 = pem
                    .replaceAll("-----BEGIN PUBLIC KEY-----", "")
                    .replaceAll("-----END PUBLIC KEY-----", "")
                    .replaceAll("\\s+", "");
            byte[] der = Base64.getDecoder().decode(b64);
            KeyFactory kf = KeyFactory.getInstance("RSA");
            k = (RSAPublicKey) kf.generatePublic(new X509EncodedKeySpec(der));
            cachedKey = k;
            return k;
        } catch (Exception e) {
            throw AuthException.unauthorized();
        }
    }
}
