# server-java (Spring Boot 3.2 / Java 17) — 多阶段、非 root、最小运行时
# 构建上下文：server-java/（独立 Maven 模块，pom 自包含）
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml .
# 预热依赖（有网时加速分层缓存；离线或失败不影响后续 package 步骤）
RUN mvn -B -e -DskipTests dependency:go-offline || true
COPY src ./src
# 镜像内跳过测试：单测/集成测试已由 CI gates 全绿验证；镜像只产出可运行 fat-jar
RUN mvn -B -e -DskipTests clean package

FROM eclipse-temurin:17-jre
WORKDIR /app
# 仅拷贝 Spring Boot repackage 产物（server-java-0.1.0.jar）
COPY --from=build /build/target/server-java-0.1.0.jar app.jar
# 健康探针依赖 curl（Debian 基础，精简安装并清 apt 缓存）
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
# 最小权限运行（固定 uid 10001），缩小容器逃逸 / 写范围事故面
RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
# 容器感知堆上限（按 512m~1g 容器预算；生产按容量调 MaxRAMPercentage）
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
