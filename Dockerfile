# 使用官方 Python 运行时作为父镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml uv.lock* ./

# 安装依赖
# 我们使用 uv 来安装依赖，因为它通常比 pip 更快
RUN pip install uv
RUN uv pip install --system --no-cache --requirement pyproject.toml

# 复制项目代码到容器中
COPY . .

# 暴露端口，以便容器外可以访问
EXPOSE 8005

# 运行 aoo.py 当容器启动时
CMD ["python", "server_StreamableHTTP.py"]
