# 保持使用官方 Playwright 镜像，这是为了稳定运行浏览器，不分家
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

# 环境变量优化
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 这里的库是根据你手动部署 OpenCloudOS 的经验总结的
RUN apt-get update && apt-get install -y \
    libzbar0 \
    default-libmysqlclient-dev \
    libgl1-mesa-glx \
    nodejs \
    npm \
    # 增加字体支持，防止抓取网页时乱码
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# 暴露 3001
EXPOSE 3001

# Gunicorn 启动。注意这里增加了 --access-logfile - 方便你在 docker logs 里看到 OpenCloudOS 风格的日志
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:3001", "n_main:n_app", "--timeout", "300", "--access-logfile", "-"]