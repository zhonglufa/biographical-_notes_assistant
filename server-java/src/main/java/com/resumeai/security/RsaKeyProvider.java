package com.resumeai.security;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

/**
 * RS256 密钥源（HLD §3.1 / ADR-017/018）。
 *
 * <p>加载策略（fail-closed 对齐 JwtVerifier）：
 * <ul>
 *   <li>public-key 与 private-key(PEM) 均配置 → 加载固定密钥对（生产：经 .env 挂载，私钥**不入库、不进镜像**）；</li>
 *   <li>两者均留空 → 生成临时 RSA-2048 密钥对（开发/测试零配置可起），并明确 WARN 日志（重启后旧令牌失效）；</li>
 *   <li>只配其一 → 启动即失败（配置不一致，避免半吊子安全）。</li>
 * </ul>
 * 签发器(JwtTokenSigner)与验签器(JwtVerifier)共用本实例的同一密钥对，保证自签自验。
 */
public class RsaKeyProvider {

    private static final Logger log = LoggerFactory.getLogger(RsaKeyProvider.class);

    private final PublicKey publicKey;
    private final PrivateKey privateKey;

    public RsaKeyProvider(String publicKeyPem, String privateKeyPem) {
        PublicKey pub = isBlank(publicKeyPem) ? null : loadPublic(publicKeyPem);
        PrivateKey priv = isBlank(privateKeyPem) ? null : loadPrivate(privateKeyPem);

        if (pub != null && priv != null) {
            this.publicKey = pub;
            this.privateKey = priv;
        } else if (pub == null && priv == null) {
            KeyPair kp = generate();
            this.publicKey = kp.getPublic();
            this.privateKey = kp.getPrivate();
            log.warn("RS256 密钥未配置(resumeai.jwt.public-key / private-key)，已生成临时 RSA-2048 密钥对（开发模式）。"
                    + " 生产必须经 .env 注入稳定 PEM，否则服务重启后已签发令牌全部失效。");
        } else {
            throw new IllegalStateException(
                    "RS256 密钥配置不一致：public-key 与 private-key 必须同时配置，或同时留空（开发临时密钥）。");
        }
    }

    public PublicKey getPublicKey() {
        return publicKey;
    }

    public PrivateKey getPrivateKey() {
        return privateKey;
    }

    private static boolean isBlank(String s) {
        return s == null || s.isBlank();
    }

    private static PublicKey loadPublic(String pem) {
        try {
            byte[] der = Base64.getDecoder().decode(strip(pem));
            return KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(der));
        } catch (Exception e) {
            throw new IllegalStateException("加载 RS256 公钥 PEM 失败", e);
        }
    }

    private static PrivateKey loadPrivate(String pem) {
        try {
            byte[] der = Base64.getDecoder().decode(strip(pem));
            return KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(der));
        } catch (Exception e) {
            throw new IllegalStateException("加载 RS256 私钥 PEM 失败", e);
        }
    }

    private static KeyPair generate() {
        try {
            KeyPairGenerator g = KeyPairGenerator.getInstance("RSA");
            g.initialize(2048);
            return g.generateKeyPair();
        } catch (Exception e) {
            throw new IllegalStateException("生成临时 RSA 密钥对失败", e);
        }
    }

    private static String strip(String pem) {
        return pem
                .replaceAll("-----BEGIN PUBLIC KEY-----", "")
                .replaceAll("-----END PUBLIC KEY-----", "")
                .replaceAll("-----BEGIN PRIVATE KEY-----", "")
                .replaceAll("-----END PRIVATE KEY-----", "")
                .replaceAll("-----BEGIN RSA PRIVATE KEY-----", "")
                .replaceAll("-----END RSA PRIVATE KEY-----", "")
                .replaceAll("\\s+", "");
    }
}
