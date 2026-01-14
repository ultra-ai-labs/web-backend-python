项目架构概览（后端）

本文档简要说明后端（`web-backend-python`）的结构、主要 HTTP 接口，以及分析任务在线程/执行体之间的关系。

架构图（ASCII）

- 总体组件：

  Client (Frontend)
      |
      | HTTP
      v
  Flask App (main.py / Blueprints)
      +-- 路由：/start-analysis (legacy), /analysis, /progress, /stop_analysis, /comments, /test_analysis ...
      |
      +-- 控制器（Blueprints）: app/controller/comment_analysis.py
      |       - 入口：`/analysis` -> 验证 -> 创建或取 TaskStep -> 在新线程中调用 CommentAnalysisService.analysis_file_by_task_id
      |       - `/progress`、`/comments`、`/stop_analysis` 等辅助接口
      |
      +-- 服务： app/services/comment_analysis_service.py
      |       - `analysis_file_by_task_id`：负责并发分析（ThreadPoolExecutor）与进度更新（独立进度线程）
      |       - 使用 OpenAI/Deepseek 进行模型调用，负责结果写回 repo
      |
      +-- Repo 层：app/repo/*.py（TaskRepo、TaskStepRepo、Douyin/XHS 评论 repo 等）
      |
      +-- DB: MySQL (持久化任务/评论/step 等)
      +-- Cache: Redis (可选，用于短期缓存、任务队列或限流)
      +-- Object Storage: Qiniu / Tencent COS（上传分析结果）

线程与执行关系（简述）

1. HTTP 请求 -> 创建任务
   - 客户端请求 `/analysis` 或 `/start-analysis`。
   - 后端验证并创建任务/TaskStep 记录。
   - 后端立即返回响应（非阻塞），并在后台启动一个新线程来执行分析。

2. 后台分析线程（顶层）
   - 在 controller（`run_analysis`）中：创建 `threading.Thread`（称为 "主分析线程"），目标为 `CommentAnalysisService.analysis_file_by_task_id` 或 `analyze_file`。
   - 主分析线程负责协调以下子任务：
       a. 启动一个进度线程（`progress_thread`），周期性统计已处理评论数并写入 TaskStep 状态（RUNNING/FINISH）。
       b. 启动一个或多个并发工作线程（线程池 `ThreadPoolExecutor`），并行对评论调用 `gpt4_analysis`/`handle_deepseek`。
       c. 每个工作线程处理单条评论：调用模型、解析 JSON、写回数据库（update_comment_by_comment_id）。
       d. 主分析线程等待所有工作线程完成后，合并结果并上传到对象存储，然后把 TaskStep 标记为 FINISH。

3. 停止（/stop_analysis）
   - Controller 的 `/stop_analysis` 调用 `CommentAnalysisService.stop_analysis(task_id, user_id)`。
   - 在 Service 内部维护一个 per-task 停止信号（例如 `threading.Event`），工作线程与进度线程会周期性检查该事件；若事件被 set，则安全退出（不再提交新任务或跳过尚未开始的评论），并将任务状态标记为已停止或保留当前进度。

主要接口（摘录）

- 分析相关（新 blueprint 风格）
  - POST `/analysis` — 接收 `AnalysisRequest`（包含 `task_id`、`analysis_request`、`output_fields`），在后台执行任务（由 `CommentAnalysisService` 处理）。
  - GET `/progress` — 查询某个 task 的进度（num / sum / state / url）。
  - POST `/stop_analysis` — 请求停止正在运行的分析任务（调用 Service 的 stop 方法）。
  - GET `/comments` — 分页获取任务下的评论及其分析结果。
  - POST `/test_analysis` — 对单条评论进行即时分析（同步，便于调试）。

- Legacy / 简单实现（在 `main.py` 中）
  - POST `/start-analysis` — 接收 `AnalysisRequest`（`file_path`、`analysis_background`、`analysis_task`、`output_fields`），在新线程内调用 `analyze_file(request_data, task_id)` 并立即返回 `task_id`。
  - GET `/analysis-progress` — 查询 `task_manager` 存储的进度；完成后可返回上传到七牛的 URL。
  - POST `/analysis-upload` — 接受文件上传（用于分析输入）。

并发/并行关键点

- 两层并发模型：
  1. 任务级并发：每个分析请求在 controller 层会 spawn 一个线程（独立执行一个任务）。
  2. 评论级并发：在任务线程内部使用 `ThreadPoolExecutor`（或循环）并发处理多条评论以加速模型请求。

- 进度更新：独立的 `progress_thread` 周期性读取数据库中的评论状态（`extra_data` 字段）来计算已完成数量并更新 `TaskStep` 表；避免在每个评论写回时触发复杂事务。

- 停止机制：Service 内维护 `stop_event`（或类似的共享标志），并在以下位置检查：
  - 在分析线程主循环（开始下一轮前）检查以中断循环。
  - 在每个工作线程开始前检查以避免开始新请求。
  - 在进度线程循环中检查以尽早退出并写入最终进度。

实践建议

- 为避免内存/资源泄露，务必在任务结束或停止后清理 per-task 的 stop_event 与临时文件路径（`task_output_paths` 或临时 CSV）。
- 模型调用失败时应有重试与熔断策略（service 中已有 `retry_on_exception` 装饰器示例）。
- 对大量并发的任务，考虑把任务交给真正的队列系统（如 Celery + Redis / RabbitMQ），把模型调用限制在受控 worker 池中。

如果你希望，我可以：
- 把上面的 ASCII 图转成 PlantUML / Mermaid 并把可视化文件加到项目中（如 `docs/architecture.puml` 或 `README.md` 中嵌入 Mermaid），或者
- 在 `web-backend-python/README.md` 中把示意图改成更详细的按模块流程图（包含 DB 表和字段示意）。
