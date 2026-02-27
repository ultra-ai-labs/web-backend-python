FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 基础系统依赖（确保 Playwright 与 Chromium 运行）
RUN apt-get update && apt-get install -y \
    libzbar0 \
    default-libmysqlclient-dev \
    libgl1-mesa-glx \
    nodejs \
    npm \
    fonts-noto-cjk \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 \
    nss nspr libxkbcommon0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 确保 Playwright 的系统依赖和 Chromium 浏览器已安装（有些基础镜像已包含，但显式安装更稳）
RUN playwright install-deps && \
    playwright install chromium

COPY . .

EXPOSE 3001

# 使用 gunicorn 启动 n_main:n_app（与 deploy_manual/手动运行 n_main.py 不冲突）
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:3001", "n_main:n_app", "--timeout", "300", "--access-logfile", "-"]