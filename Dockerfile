# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    sqlite3 curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY entrypoint.sh .
COPY app/ ./app/
COPY static/ ./static/

# 设置权限
RUN chmod +x /app/entrypoint.sh

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data

# 复制并设置下载脚本权限
COPY app/scripts/download_data.sh /app/app/scripts/
RUN chmod +x /app/app/scripts/download_data.sh

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口 (uvicorn 默认使用 8000)
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]