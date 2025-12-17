# Env 与凭据使用说明（自动记录）

此文档由助手自动生成，记录在 `MediaCrawler-main` 中发现的硬编码凭据、使用位置、风险评估与建议。用于后续改造为基于环境变量的配置。

## 一、发现摘要

- 文件：`config/base_config.py` 包含多项硬编码配置（非仅示例），包括七牛、腾讯 COS、OpenAI、Deepseek 等密钥，以及若干爬虫运行默认值。
- 在代码中，这些常量被 `config` 包通过 `from .base_config import *` 暴露，全库模块通过 `import config` 直接使用。
- 部分模块还有重复硬编码（例如 `main.py` 顶部也含有七牛凭据），存在重复/分散的风险。

## 二、硬编码项（来自 `config/base_config.py`）

- 爬虫默认配置：`PLATFORM`, `KEYWORDS`, `LOGIN_TYPE`, `HEADLESS`, `SAVE_LOGIN_STATE`, `SAVE_DATA_OPTION`, `USER_DATA_DIR`, `START_PAGE`, `CRAWLER_MAX_NOTES_COUNT`, `MAX_CONCURRENCY_NUM`, `ENABLE_GET_IMAGES`, `ENABLE_GET_COMMENTS`, `ENABLE_GET_SUB_COMMENTS`
- 代理与池配置：`ENABLE_IP_PROXY`, `IP_PROXY_POOL_COUNT`, `IP_PROXY_PROVIDER_NAME`
- 七牛（Qiniu）凭据/配置：`AccessKey`, `SecretKey`, `BucketName`, `CDNTestDomain`
- 腾讯 COS：`TencentSecretId`, `TencentSecretKey`, `TencentBucketName`, `TencentCdnDomain`, `TencentRegion`
- LLM：`OPENAI_API_KEY`, `DEEPSEEK_API_KEY`
- 并发控制：`ANALYSIS_THREAD_NUM`

（注：上述字符串如 `OPENAI_API_KEY` 看起来像真实 key 的格式，不应提交到版本库）

## 三、主要使用位置

- `MediaCrawler-main/app/services/comment_analysis_service.py`
  - 使用 `config.AccessKey` / `config.SecretKey` 初始化 `qiniu.Auth`。
  - 使用 `config.BucketName` / `config.CDNTestDomain` 在 `upload_to_qiniu()` 中构造返回 URL。
  - 使用 `config.TencentSecretId` / `config.TencentSecretKey` / `config.TencentRegion` 初始化 `CosConfig`，使用 `config.TencentBucketName` / `config.TencentCdnDomain` 构造腾讯上传 URL。
  - 使用 `config.OPENAI_API_KEY` 与 `config.DEEPSEEK_API_KEY` 进行模型请求（`gpt4_analysis`、`handle_deepseek`）。

- `MediaCrawler-main/main.py`
  - 文件顶部存在重复的七牛凭据常量（`AccessKey`, `SecretKey`, `BucketName`），并直接用 `qiniu.Auth(...)` 初始化。与 `base_config.py` 重复。

- `MediaCrawler-main/config/__init__.py`
  - 通过 `from .base_config import *` 导出所有 `base_config` 常量，使其在 `import config` 后可直接访问。

- 其他模块（爬虫、代理池等）读取 `config` 中的运行项配置（如 `HEADLESS`, `IP_PROXY_PROVIDER_NAME`, `ANALYSIS_THREAD_NUM` 等）。

## 四、风险与问题

- 明文密钥泄露风险：公开仓库或多人协作时，真实密钥已存在仓库文件中可能造成泄露。
- 可维护性差：凭据分散在多个文件（且有重复），环境切换（dev/prod）不便。
- 审计与撤销成本高：若密钥已公开，需要逐一撤销并替换。

## 五、建议（短期/长期）

短期（建议立刻做）：
- 将 `.env.example` 放入仓库（已添加），并把真实凭据移入私有 `.env`（并将 `.env` 加入 `.gitignore`）。
- 针对已提交的真实密钥，评估是否需要撤销并替换（如果是真密钥）。

长期（安全化改造）：
1. 修改 `config/base_config.py`：优先通过 `os.getenv('VAR_NAME', '<fallback>')` 读取敏感配置，保留合理的默认值或空字符串作为回退。 
2. 移除 `main.py` 等处的重复硬编码，统一从 `config` 读取配置，减少重复来源。 
3. 在应用启动时增加环境变量校验（对必须的密钥进行检测，未配置则抛错并提示）。
4. 考虑将生产密钥放在机密管理系统（如 HashiCorp Vault、云平台 Secrets Manager）并在部署时注入。 

## 六、下一步（我可以帮你做的事）

- 如果你同意，我可以提交一个 patch：
  - 将 `config/base_config.py` 改为优先读取环境变量（保留当前值作为注释/默认），
  - 并修改 `MediaCrawler-main/main.py` 中重复硬编码为使用 `config`（不删除功能，仅统一来源）。
- 或者我可以先只把 `base_config.py` 生成一个安全化示例（不会修改其他文件），供你审阅。

---
生成时间：2025-12-01  本记录仅作代码审计与改造参考，不会自动替换任何运行时凭据。
