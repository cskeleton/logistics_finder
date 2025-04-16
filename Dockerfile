# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目代码到工作目录
COPY ./app /app/app
COPY ./static /app/static
# 如果你的主入口文件不在 app/ 目录下，也需要复制
# COPY main.py /app/

# 暴露端口 (uvicorn 默认使用 8000)
EXPOSE 8000

# 运行 uvicorn 服务器
# 注意：确保你的主应用实例是 app/main.py 中的 app 对象
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]