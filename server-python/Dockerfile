# server-python FastAPI 服务（ADR-002：Python LLM 网关 + 本机 Agent 触发路由）
#
# 运行时依赖 design/contracts（config.load_sla_from_contract / contracts.validate_* 启动时加载 SLA 与校验载荷），
# 故必须保留「server-python/ 与 design/ 为兄弟目录」的布局，使 app 内 _REPO_ROOT 上溯 3 层能定位到 design/contracts。
# 这与根 Dockerfile 构建 scaffold 的模式一致。
FROM python:3.13-slim

WORKDIR /app

# design/contracts 为运行时真相源（零第三方依赖的契约校验器），需一并拷贝
COPY design /app/design
COPY server-python /app/server-python

WORKDIR /app/server-python

# 仅装运行所需依赖（锁定大版本，避免意外升级引入破坏性变更）
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "fastapi>=0.110" "uvicorn>=0.27" "pydantic>=2.6" "httpx>=0.27"

ENV PORT=8000 \
    HOST=0.0.0.0

EXPOSE 8000

# 最小权限运行，缩小生产事故面（容器逃逸 / 写文件范围受限）
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
