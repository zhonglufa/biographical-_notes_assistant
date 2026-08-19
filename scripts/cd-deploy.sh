#!/bin/sh
# cd-deploy.sh — 轻量 CD（O2 · 运维采纳结论：CD 做轻量版）
#
# 职责：合并到 master 后，构建「单机器 / 小容器」部署包（前端 + server-java fat-jar + server-python），
#       并给出可复现的镜像构建 / 上线步骤。做到「生产就绪脚本」级。
# 不真部署：任何对外动作（docker push / ssh 发布 / 拉起服务）均受 $DEPLOY_TOKEN 门控；
#   无凭据时仅本地打包并打印人工上线步骤，绝不静默触达生产。
#
# 设计依据（PROJECT_BRAIN §4 运维取舍）：CI 必留 / CD 轻量 / 监控必要 / K8s 现阶段不要。
# ⚠️ 部署上线、提供真实凭据属用户独有动作，本脚本不伪造部署完成。
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BUILD_DIR="$ROOT/dist-cd"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "▶ [CD] 1/4 构建前端（Vue 3 + Vite）"
if [ -d frontend ] && [ -f frontend/package.json ]; then
  ( cd frontend && npm ci && npm run build )
  cp -r frontend/dist "$BUILD_DIR/frontend"
  echo "    前端产物 -> $BUILD_DIR/frontend"
else
  echo "    ⚠ 未找到 frontend，跳过前端构建"
fi

echo "▶ [CD] 2/4 打包 server-java（Spring Boot fat-jar）"
if [ -d server-java ] && [ -f server-java/pom.xml ]; then
  ( cd server-java && mvn -B -DskipTests clean package )
  mkdir -p "$BUILD_DIR/server-java"
  cp server-java/target/server-java-0.1.0.jar "$BUILD_DIR/server-java/"
  echo "    server-java 产物 -> $BUILD_DIR/server-java/server-java-0.1.0.jar"
else
  echo "    ⚠ 未找到 server-java，跳过"
fi

echo "▶ [CD] 3/4 打包 server-python（FastAPI + 契约真相源 design/contracts）"
if [ -d server-python ] && [ -f server-python/app/main.py ]; then
  mkdir -p "$BUILD_DIR/server-python"
  cp -r server-python/app "$BUILD_DIR/server-python/app"
  cp server-python/pyproject.toml "$BUILD_DIR/server-python/" 2>/dev/null || true
  cp -r design "$BUILD_DIR/server-python/design" 2>/dev/null || true
  echo "    server-python 产物 -> $BUILD_DIR/server-python"
else
  echo "    ⚠ 未找到 server-python，跳过"
fi

# 生成可复现的部署清单
( cd "$BUILD_DIR" && find . -type f | sort > MANIFEST.txt )
echo "    部署清单 -> $BUILD_DIR/MANIFEST.txt"

echo "▶ [CD] 4/4 部署门控"
if [ -n "${DEPLOY_TOKEN:-}" ]; then
  echo "    ✅ 检测到 DEPLOY_TOKEN：构建镜像（不自动 push / 发布，真实发布由运维按权限执行）。"
  echo "    镜像构建（需在目标机或 CI runner 执行）："
  echo "      docker compose --env-file .env build"
  echo "      # 或单服务："
  echo "      docker build -t resume-ai-server-java:\$(git rev-parse --short HEAD) -f server-java/Dockerfile server-java"
  echo "      docker build -t resume-ai-server-python:\$(git rev-parse --short HEAD) -f server-python/Dockerfile ."
else
  echo "    ⏸ 未提供 DEPLOY_TOKEN：仅本地打包完成，不触达生产。"
  echo "    人工上线步骤（用户/运维执行）："
  echo "      1) 目标机准备 Docker + Docker Compose（及 Node 仅用于前端构建，可走镜像）"
  echo "      2) 复制 $BUILD_DIR 与 .env 到目标机"
  echo "      3) 配置 .env：DB_PASS / RESIMEAI_JWT_* / INTERNAL_TOKEN / LLM_API_KEY / 护栏阈值"
  echo "      4) docker compose --env-file .env up -d --build"
  echo "      5) 校验：curl /actuator/health（java）、/healthz（python）、前端 http://host:5173"
  echo "      6) 接入真实平台账号（用户本机浏览器自动化，服务端不持凭据）"
  echo "      7) 配置 Prometheus 抓取 /metrics（若启用）"
fi

echo "✅ [CD] 轻量部署包构建完成（生产就绪脚本，未真部署）。"
