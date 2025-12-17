# 使用 Playwright 官方基础镜像
FROM mcr.microsoft.com/playwright/python:v1.22.0-focal

# 设置工作目录
WORKDIR /app

# 复制当前目录的内容到工作目录
COPY . /app

# 设置 pip 使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Python 依赖
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 安装 Playwright 依赖并设置环境变量使用国内镜像
RUN apt-get update && apt-get install -y wget gnupg
RUN wget -qO- https://deb.playwright.dev/gpg | apt-key add -
RUN echo "deb https://deb.playwright.dev/ focal main" | tee /etc/apt/sources.list.d/playwright.list
RUN apt-get update && apt-get install -y playwright

# 设置 Playwright 使用国内镜像
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npm.taobao.org/mirrors

# 安装 Playwright 浏览器
RUN playwright install

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "test_main:n_app"]
