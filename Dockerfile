# ---- Stage 1: Builder ----
# 使用一个构建阶段来安装依赖，这样可以更好地利用缓存
FROM python:3.13-slim AS builder

WORKDIR /app

# 设置环境变量，避免安装时出现交互式提示
ENV DEBIAN_FRONTEND=noninteractive
# 确保pip不缓存，减小镜像体积
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装构建系统依赖（如果需要）
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# 仅复制依赖定义文件
# 这样，只有在依赖变化时，这一层缓存才会失效
COPY pyproject.toml .

# 安装依赖项到 /install 目录
# 使用 `pip install .` 会从 pyproject.toml 读取依赖
RUN pip install --target=/install .


# ---- Stage 2: Final Image ----
# 使用一个新的、干净的基础镜像作为最终镜像
FROM python:3.13-slim

# 创建一个非 root 用户来运行应用，提高安全性
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser
WORKDIR /home/appuser/app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# 将安装的依赖路径添加到 PYTHONPATH
ENV PYTHONPATH=/home/appuser/install

ENV PATH=/home/appuser/install/bin:$PATH
# 从构建阶段复制已安装的依赖
COPY --from=builder /install /home/appuser/install

# 复制应用代码
COPY . .

# 创建数据目录并声明为一个卷，用于持久化数据
VOLUME /home/appuser/data

# 暴露端口
EXPOSE 8005

# 健康检查（指向我们将在应用中添加的 /health 端点）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# 启动命令
# 注意：文件名应为 server.py 或您实际的文件名
CMD ["uvicorn", "server_StreamableHTTP:app", "--host", "0.0.0.0", "--port", "8005"]

