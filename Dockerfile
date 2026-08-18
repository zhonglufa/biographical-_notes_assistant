# resume-ai-prod 服务端轻量容器（O 阶段 · 上线就绪）
# 零第三方依赖：仅 Python 标准库；契约校验器复用 design/contracts（纯标准库）。
FROM python:3.13-slim

WORKDIR /app

# 目录层级必须保持 scaffold/src + design，使 contract_runtime 能向上定位 design/contracts。
# 若改为 COPY scaffold/src，则 contract_runtime 计算的 _REPO_ROOT 会错位导致校验器找不到 schema。
COPY scaffold /app/scaffold
COPY design /app/design

ENV PORT=8080 \
    HOST=0.0.0.0

EXPOSE 8080

# 最小权限运行，缩小生产事故面（容器逃逸/写文件范围受限）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "scaffold/src/server_main.py"]
