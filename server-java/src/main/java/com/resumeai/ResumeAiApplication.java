package com.resumeai;

import com.resumeai.config.JwtProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

/**
 * Resume AI 业务侧入口（Java Spring Boot 模块化单体）。
 * 依据 HLD ADR-001（模块化单体）+ ADR-002（双语言异构业务侧）。
 * 浏览器自动化不在本进程（已下沉本机 Agent，见 ADR-003）。
 */
@SpringBootApplication
@EnableConfigurationProperties(JwtProperties.class)
public class ResumeAiApplication {
    public static void main(String[] args) {
        SpringApplication.run(ResumeAiApplication.class, args);
    }
}
