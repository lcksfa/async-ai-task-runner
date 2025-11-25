
### 📅 Day 1: 骨架与数据 (FastAPI + SQL)
**核心任务**：建立 API 服务，并实现数据的持久化存储。

#### 🌅 上午：FastAPI 与 Pydantic 基础
*   **学习重点**：
    *   FastAPI 的路由（Routes）与依赖注入（Dependency Injection）。
    *   Pydantic 的数据验证（Schema Validation）：为什么 Type Hints 很重要。
*   **实践**：
    *   创建一个 `/health` 接口。
    *   创建一个 `/tasks` POST 接口，接收 JSON 数据（如 `{"prompt": "...", "model": "gpt-4"}`），利用 Pydantic 拦截格式错误。
*   **🤖 AI 助攻指令**：
    *   “我是 FastAPI 新手，请用 Pydantic 定义一个 `TaskCreate` 模型，包含 prompt (str) 和 priority (int)，并写一个 POST 路由来接收它。”
    *   “解释一下 Pydantic 的 `BaseModel` 和 Python 原生 `dataclass` 的区别。”

#### 🌇 下午：PostgreSQL 与 Alembic
*   **学习重点**：
    *   ORM (SQLAlchemy) vs Raw SQL。
    *   Alembic 的作用：像 Git 管理代码一样管理数据库结构的变更。
*   **实践**：
    *   本地安装 PostgreSQL。
    *   定义 `Task` 数据库模型（ID, status, result, created_at）。
    *   使用 Alembic 初始化并生成第一个迁移文件（Migration）。
    *   在 API 中实现：接收请求 -> 存入数据库（状态为 `PENDING`） -> 返回 Task ID。
*   **🤖 AI 助攻指令**：
    *   “请帮我配置 FastAPI 和 SQLAlchemy 的异步连接字符串（Asyncpg）。”
    *   “我修改了模型字段，如何用 Alembic 生成新的迁移脚本？”

---

### 📅 Day 2: 异步与解耦 (Celery + Redis)
**核心任务**：解决“LLM 太慢会卡死 HTTP 请求”的问题。

#### 🌅 上午：理解异步与事件驱动
*   **学习重点**：
    *   同步 (Sync) vs 异步 (Async) 的区别。
    *   为什么需要消息队列（Message Queue）？(Producer-Consumer 模式)。
    *   安装 Redis 作为 Celery 的 Broker。
*   **实践**：
    *   画出架构图：API (Producer) -> Redis (Queue) -> Worker (Consumer)。
    *   配置基本的 Celery 实例。
*   **🤖 AI 助攻指令**：
    *   “请用通俗的比喻解释 Message Queue 在 Web 开发中的作用。”
    *   “如何用 Docker 快速启动一个 Redis 容器供本地开发使用？”

#### 🌇 下午：集成 Celery 后台任务
*   **学习重点**：
    *   定义 Celery Task。
    *   在 FastAPI 中调用 `task.delay()`。
*   **实践**：
    *   编写一个模拟耗时任务 `run_ai_generation(prompt)`（用 `time.sleep(5)` 模拟）。
    *   修改 Day 1 的 API：收到请求后，**不等待**结果，直接触发 Celery 任务，并立即返回 Task ID。
    *   Worker 完成任务后，更新数据库中的状态为 `COMPLETED` 并写入结果。
*   **🤖 AI 助攻指令**：
    *   “FastAPI 是异步的，Celery 是同步的，这两者如何在一个项目中结合？请给出代码示例。”
    *   “我的 Celery Worker 接收不到任务，请帮我列出排查步骤。”

---

### 📅 Day 3: 容器化与配置 (Docker)
**核心任务**：解决“在我机器上能跑，在你机器上跑不了”的问题。

#### 🌅 上午：配置管理与安全性
*   **学习重点**：
    *   `.env` 文件与 `python-dotenv`。
    *   永远不要把 API Key 提交到 GitHub。
*   **实践**：
    *   将数据库 URL、Redis URL、OpenAI API Key 全部移入环境变量。
    *   在 FastAPI 中创建一个 `Settings` 类来统一管理配置。
*   **🤖 AI 助攻指令**：
    *   “请检查我的代码，看有没有硬编码的敏感信息？”
    *   “如何在 Pydantic 中使用 `BaseSettings` 来读取环境变量？”

#### 🌇 下午：Docker 与 Docker Compose
*   **学习重点**：
    *   `Dockerfile` 编写（构建镜像）。
    *   `docker-compose.yml` 编排（同时启动 Web, Worker, Postgres, Redis）。
*   **实践**：
    *   编写 Dockerfile。
    *   编写 docker-compose. yml，实现一条命令 `docker-compose up` 启动整个系统。
    *   验证容器间的网络通信（Web 容器能否连上 DB 容器？）。
*   **🤖 AI 助攻指令**：
    *   “请帮我写一个适用于 Python 3.11 FastAPI 项目的轻量级 Dockerfile。”
    *   “解释 docker-compose 中的 `depends_on` 和 `networks` 是什么意思。”

---

### 📅 Day 4: 扩展 AI 能力 (MCP Server)
**核心任务**：理解并实现 Model Context Protocol，让你的后端能被其他 AI 客户端（如 Claude Desktop）连接。

#### 🌅 上午：理解 MCP (Model Context Protocol)
*   **学习重点**：
    *   MCP 是什么？（标准化 AI 连接数据的协议）。
    *   MCP 的 Resource, Prompt, Tool 概念。
*   **实践**：
    *   阅读 MCP 官方文档或观看介绍视频。
    *   分析你的后端有哪些数据可以暴露给 AI？（例如：查询历史任务记录）。
*   **🤖 AI 助攻指令**：
    *   “请用简单的语言解释 MCP 协议解决了什么问题？”
    *   “MCP Server 和我现有的 FastAPI Server 有什么关系？”

#### 🌇 下午：构建简单的 MCP Server
*   **学习重点**：
    *   使用 Python SDK 构建 MCP Server。
*   **实践**：
    *   创建一个独立的 MCP 服务（或集成在现有应用中）。
    *   暴露一个 Tool：`get_task_status(task_id)`。
    *   尝试用 Claude Desktop 或其他支持 MCP 的客户端连接你的本地服务，让 Claude 能查询你数据库里的任务状态。
*   **🤖 AI 助攻指令**：
    *   “请给我一个最简单的 Python MCP Server 示例，暴露一个加法工具。”
    *   “如何调试 MCP Server 和客户端之间的通信？”

---

### 📅 Day 5: 综合实战与重构
**核心任务**：将 Day 4-5 的 CLI 逻辑移植到这个强大的后端架构中。

#### 🌅 上午：移植核心逻辑
*   **实践**：
    *   将你之前的 `Time Tool`, `Calculator`, `File Writer` 逻辑移植到 Celery Task 中。
    *   现在，用户通过 API 发送 "计算 1+1"，FastAPI 接收 -> Celery 执行 -> 结果存入 Postgres。
*   **🤖 AI 助攻指令**：
    *   “如何优雅地处理 Celery 任务中的异常，并将错误信息保存到数据库？”

#### 🌇 下午：API 文档与测试
*   **实践**：
    *   完善 FastAPI 自动生成的 Swagger UI (`/docs`)。
    *   使用 `pytest` 编写一个集成测试：发送请求 -> 轮询数据库直到任务完成 -> 验证结果。
    *   **最终验收**：你的系统现在是一个异步、容器化、持久化的 AI 任务处理平台。
*   **🤖 AI 助攻指令**：
    *   “请帮我为这个 API 接口生成标准的 OpenAPI 文档描述。”
    *   “如何用 pytest 测试一个依赖数据库的异步接口？”
