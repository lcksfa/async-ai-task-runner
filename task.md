
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
    *   本地通过 Docker 安装 PostgreSQL。
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

#### 🌇 下午：AI API，Docker 与 Docker Compose
*   **学习重点**：
    *    接入真实 AI：接入 deepseek 模型，让它真正为你生成内容。
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

#### 🌅 上午：理解协议与设计接口

**1. 理论学习：什么是 MCP？**
*   **核心概念**：
    *   **MCP Server**：提供数据（Resources）和功能（Tools）的服务端（我们要写的）。
    *   **MCP Client**：使用这些能力的客户端（如 Claude Desktop, Cursor, IDEs）。
    *   **Transport**：它们怎么交流？通常通过 `stdio`（标准输入输出）进行本地通信。
*   **为什么重要**：以前我们要让 ChatGPT 操作数据库，需要把数据库导出来或者写很复杂的 Plugin。MCP 让这变成了一个标准化的 Python 脚本。

**2. 需求分析：我们要暴露什么给 AI？**
我们需要把 Day 1-3 做的功能封装成 **Tools（工具）**：
*   `submit_task(prompt, model)`: 允许 AI 帮我们提交生成任务。
*   `get_task_status(task_id)`: 允许 AI 查询任务进度和结果。
*   `list_recent_tasks(limit)`: 允许 AI 查看最近的任务列表。

**3. 环境准备**
*   安装 MCP 的 Python SDK。
*   确保昨天的 Docker 环境（FastAPI + Redis + Postgres + Worker）正在运行，因为我们的 MCP Server 将通过 HTTP 请求与它们交互。

---

#### 🌇 下午：代码实现与端到端连接

**1. 编写 MCP Server (`app/mcp_server.py`)**
*   **技术选型**：使用 `mcp` 官方库中的 `FastMCP`（类似 FastAPI 的高层封装）。
*   **逻辑实现**：
    *   创建一个 MCP 实例。
    *   使用装饰器 `@mcp.tool()` 定义工具函数。
    *   在工具函数内部，使用 `httpx` 库向 `http://localhost:8000` 发起请求（复用我们现有的 API）。
    *   *注意：这里我们不直接连数据库，而是通过 API 交互，模拟“AI 是一个用户”的场景，这样更安全且逻辑解耦。*

**2. 配置 Claude Desktop**
*   找到 Claude Desktop 的配置文件（通常在 `~/Library/Application Support/Claude/claude_desktop_config.json` 或 Windows 对应目录）。
*   注册我们的 Server：告诉 Claude 启动命令是 `uv run app/mcp_server.py`。

**3. 调试与实战**
*   **调试**：使用 MCP Inspector（官方调试工具）来测试工具是否能被正确识别。
*   **实战对话**：
    *   打开 Claude Desktop。
    *   输入：“请帮我生成一个关于‘量子力学’的简介，使用 gpt-4 模型。”
    *   观察：Claude 是否请求调用 `submit_task` 工具？
    *   输入：“刚才那个任务 ID 是多少？帮我查查它做完了吗？”
    *   观察：Claude 是否调用 `get_task_status` 并把结果读给你听。

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
