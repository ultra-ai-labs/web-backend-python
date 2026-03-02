# Ultra AI Backend - 环境配置说明

## 快速开始

### 1. 创建环境变量文件

```bash
cp .env.example .env
```

### 2. 配置必要的环境变量

编辑 `.env` 文件，填入实际的配置值：

#### 数据库配置（必需）
```env
ENVIRONMENT=production
PROD_DB_USER=root
PROD_DB_PWD=your_password
PROD_DB_URI=127.0.0.1
PROD_DB_PORT=3306
PROD_DB_NAME=media_crawler
```

或使用直接连接字符串：
```env
RELATION_DB_URL=mysql://root:password@127.0.0.1:3306/media_crawler
```

#### 存储配置（必需）

**七牛云存储：**
```env
QINIU_ACCESS_KEY=your_actual_key
QINIU_SECRET_KEY=your_actual_secret
QINIU_BUCKET_NAME=your_bucket_name
QINIU_CDN_DOMAIN=your_cdn_domain
```

**腾讯云存储（可选）：**
```env
TENCENT_SECRET_ID=your_tencent_id
TENCENT_SECRET_KEY=your_tencent_key
TENCENT_BUCKET_NAME=your_bucket
TENCENT_CDN_DOMAIN=your_cdn_domain
TENCENT_REGION=ap-guangzhou
```

#### AI API配置（按需）
```env
OPENAI_API_KEY=sk-your-openai-key
DEEPSEEK_API_KEY=sk-your-deepseek-key
```

#### 安全配置（推荐）
```env
JWT_SECRET_KEY=generate_a_random_string_here
ADMIN_PASSWORD=your_admin_password
```

### 3. 使用 Docker Compose 启动

```bash
docker-compose up -d --build
```

### 4. 验证服务运行

```bash
curl http://localhost:3001/health
```

应该返回：
```json
{
  "status": "ok",
  "time": "2026-02-27T12:00:00Z"
}
```

## 环境变量说明

### 核心配置
- `ENVIRONMENT`: 运行环境，`production` 或 `development`
- `SAVE_DATA_OPTION`: 数据保存方式，`db` / `csv` / `json`
- `PLATFORM`: 爬虫平台，`xhs` / `douyin` / `kuaishou` / `bilibili` / `weibo`
- `LOGIN_TYPE`: 登录方式，`qrcode` / `phone` / `cookie`
- `HEADLESS`: 无头浏览器模式，`true` / `false`

### IP代理配置
- `ENABLE_IP_PROXY`: 是否启用IP代理，`true` / `false`
- `IP_PROXY_POOL_COUNT`: 代理池数量，默认 `2`
- `IP_PROXY_PROVIDER_NAME`: 代理提供商，如 `kuaidaili`

### 分析配置
- `ANALYSIS_THREAD_NUM`: 分析线程数，默认 `6`

## 注意事项

1. **不要提交 `.env` 文件到版本控制系统**
   - `.env` 已在 `.gitignore` 中
   - 只提交 `.env.example` 作为模板

2. **生成强随机密钥**
   ```bash
   # 生成 JWT Secret Key
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Docker 挂载卷**
   - `browser_data/`: 浏览器用户数据
   - `static/`: 静态文件
   - `store/`: 数据存储

4. **健康检查**
   - 端点: `GET /health`
   - 间隔: 60秒
   - 超时: 10秒

## 常见问题

### 数据库连接失败
- 检查数据库是否运行
- 验证连接字符串格式
- 确认用户权限

### 存储上传失败
- 验证七牛云/腾讯云密钥
- 检查存储桶名称和权限
- 确认CDN域名配置正确

### Docker 容器无法启动
```bash
# 查看日志
docker-compose logs -f backend

# 重建容器
docker-compose down
docker-compose up -d --build
```

## 开发模式

本地开发时直接运行：
```bash
python n_main.py
```

确保已安装依赖：
```bash
pip install -r requirements.txt
```
