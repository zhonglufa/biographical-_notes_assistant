#!/bin/sh
# cd-deploy.sh — 轻量 CD（O2 · 运维采纳结论：CD 做轻量版）
#
# 职责：合并到 master 后，自动构建「单机器 / 小容器」部署包，做到「生产就绪脚本」级。
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

echo "▶ [CD] 1/3 构建前端（Vue 3 + Vite）"
if [ -d frontend ] && [ -f frontend/package.json ]; then
  ( cd frontend && npm ci && npm run build )
  cp -r frontend/dist "$BUILD_DIR/frontend"
  echo "    前端产物 -> $BUILD_DIR/frontend"
else
  echo "    ⚠ 未找到 frontend，跳过前端构建"
fi

echo "▶ [CD] 2/3 打包服务端（Python 零依赖桩 + 监控接入点）"
mkdir -p "$BUILD_DIR/server"
cp -r scaffold/src "$BUILD_DIR/server/src" 2>/dev/null || true
cp -r design "$BUILD_DIR/server/design" 2>/dev/null || true
cp scripts/export_metrics.py "$BUILD_DIR/server/" 2>/dev/null || true
# 生成可复现的部署清单
( cd "$BUILD_DIR" && find . -type f | sort > MANIFEST.txt )
echo "    服务端产物 -> $BUILD_DIR/server ; 清单 -> $BUILD_DIR/MANIFEST.txt"

echo "▶ [CD] 3/3 部署门控"
if [ -n "${DEPLOY_TOKEN:-}" ]; then
  echo "    ✅ 检测到 DEPLOY_TOKEN：此处由运维接入真实发布（docker push / ssh / 拉起）。"
  echo "    （本次自动化循环不执行真实发布；真实上线由用户触发并提供凭据。）"
  # 真实发布示例（由运维按需启用，循环不自动执行）：
  # docker build -t rat-server:$(git rev-parse --short HEAD) -f Dockerfile . && \
  # docker push rat-server:$(git rev-parse --short HEAD) && \
  # ssh deploy@host "pull-and-restart.sh"
else
  echo "    ⏸ 未提供 DEPLOY_TOKEN：仅本地打包完成，不触达生产。"
  echo "    人工上线步骤（用户/运维执行）："
  echo "      1) 在目标机器准备 Python 3.13 + Node 运行时"
  echo "      2) 将 $BUILD_DIR 拷贝至目标机器"
  echo "      3) 配置 LLM 日硬上限金额 / 监控阈值（护栏 2/3 生产值）"
  echo "      4) 启动服务端（scaffold/src/server_main.py）与前端静态服务（frontend/dist）"
  echo "      5) 接入真实平台账号（用户本机浏览器自动化，服务端不持凭据）"
  echo "      6) 配置 Prometheus 抓取 scripts/export_metrics.py 输出（/metrics）"
fi

echo "✅ [CD] 轻量部署包构建完成（生产就绪脚本，未真部署）。"
