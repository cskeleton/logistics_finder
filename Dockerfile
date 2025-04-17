# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY app/ ./app/
COPY static/ ./static/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data

# 复制并设置下载脚本权限
COPY app/scripts/download_data.sh /app/scripts/
RUN chmod +x /app/scripts/download_data.sh

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口 (uvicorn 默认使用 8000)
EXPOSE 8000

# 运行 uvicorn 服务器
# 注意：确保你的主应用实例是 app/main.py 中的 app 对象
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]