# TokenRouter DeepSeek Flash 接入设计

## 目标

将评论分析模型从百度千帆 ERNIE 切换到 TokenRouter 的 DeepSeek V4 Flash-0731，同时继续复用项目现有的 OpenAI 兼容调用链。接入完成后，单条评论分析与批量评论分析使用同一套模型配置，不再依赖无关的 OpenAI 密钥，也不会在失败时把评论内容发送到旧的 Replit 模型代理。

## 官方接口约束

- API Base URL：`https://api.tokenrouter.cheap/v1`
- 模型 ID：`deepseek-v4-flash-0731`
- 调用端点：`POST /v1/chat/completions`
- 鉴权：`Authorization: Bearer <TOKENROUTER_API_KEY>`
- 输入：纯文本消息
- 输出：文本；本项目继续从 `choices[0].message.content` 读取 JSON 文本并在客户端解析

## 配置设计

新增 `TOKENROUTER_API_KEY` 配置项，并按以下顺序解析模型密钥：

1. `LLM_API_KEY`
2. `TOKENROUTER_API_KEY`
3. `DEEPSEEK_API_KEY`

本地未跟踪的 `.env` 负责保存真实密钥，并配置：

```env
TOKENROUTER_API_KEY=<secret>
LLM_BASE_URL=https://api.tokenrouter.cheap/v1
LLM_MODEL=deepseek-v4-flash-0731
```

受版本控制的 `.env.example` 只提供占位值和说明，不保存真实密钥。Docker Compose 继续通过现有 `env_file: .env` 注入配置。

## 调用链修改

`config/base_config.py` 负责读取 TokenRouter 密钥并生成统一的 `LLM_API_KEY`。`app/services/comment_analysis_service.py` 的 `call_llm()` 保持为唯一模型请求入口，继续使用 OpenAI Python SDK 和 `chat.completions.create()`。

单条评论分析中的旧 `OPENAI_API_KEY` 非空校验、全局赋值和未使用的 OpenAI Client 将被删除。单条分析构造消息后直接调用统一入口，与批量分析保持一致。

批量分析重试失败时，不再调用硬编码的 Replit 模型代理。失败处理只生成现有的默认结构化结果并记录错误，确保评论数据不会发送到未配置的第三方服务。

## 错误处理

- 未配置任何可用模型密钥时，在发起请求前抛出明确的配置错误。
- TokenRouter 网络或 API 错误继续由现有重试机制处理。
- 模型返回无法解析的 JSON 时，继续使用现有客户端校验和默认结果逻辑。
- 不在日志、测试输出或异常消息中打印 API Key。

## 测试与验证

自动化测试覆盖：

- 仅设置 `TOKENROUTER_API_KEY` 时可生成统一的 `LLM_API_KEY`。
- 显式 `LLM_API_KEY` 的优先级高于 TokenRouter 和 DeepSeek 密钥。
- TokenRouter 密钥优先于旧 DeepSeek 密钥。
- 单条评论分析不再要求 `OPENAI_API_KEY`。
- 失败回退不会调用旧 Replit 代理。

本地验证包括：

- 运行相关单元测试与现有测试集。
- 使用已配置的 TokenRouter Key 请求 `GET /v1/models`，确认 `deepseek-v4-flash-0731` 对当前密钥可见。
- 发送一条不包含用户数据的最小 Chat Completions 请求并确认取得有效回复。
- 验证过程只输出状态、模型 ID 和响应是否有效，不输出密钥。

## 非目标

- 不新增前端模型选择界面。
- 不引入独立的 TokenRouter SDK 或 Provider 抽象层。
- 不启用流式输出、Responses API、工具调用或图片输入。
- 不修改爬虫、数据库或评论分析提示词。
