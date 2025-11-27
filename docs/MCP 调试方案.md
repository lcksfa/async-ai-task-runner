没问题！调试是开发 MCP Server 中最容易让人抓狂但也最关键的一环。因为 MCP 运行在后台，如果出了错，你往往看不见报错信息。

为了确保你能顺利跑通，我将把 **调试** 和 **实战** 拆解成保姆级的详细步骤。

---

### 🛠️ 第一阶段：使用 MCP Inspector 进行“白盒测试”

在把你的 Server 交给 Claude 之前，我们要先用官方的调试器（Inspector）确保它本身是工作的。Inspector 是一个网页版的工具，能让你直观地看到 Server 暴露了哪些工具，并能手动点击测试。

#### 1. 安装 Inspector
确保你已经安装了 `uv`（我们在 Day 3 用过）。
```bash
# 在终端执行，安装 mcp-inspector
npm install -g @modelcontextprotocol/inspector
```

#### 2. 启动 Inspector
假设你的 MCP 代码文件是 `run_mcp_server.py`。
在终端运行：
```bash
# 这里的命令意思是：启动 inspector，让它去运行你的 python 脚本
npx @modelcontextprotocol/inspector uv run app/run_mcp_server.py
```
*(注：如果你没有安装 node/npx，也可以尝试直接用 python 运行 inspector，但推荐使用 npx 方式因为官方文档最全。如果报错，请告诉我你的环境)*

#### 3. 浏览器调试
运行成功后，终端会显示一个 URL（通常是 `http://localhost:5173`）。在浏览器打开它。

*   **检查连接**：左上角应该显示 "Connected"。
*   **查看工具 (Tools)**：
    *   点击 "Tools" 标签页。
    *   你应该能看到你定义的函数名，比如 `submit_task` 和 `get_task_status`。
    *   如果你没看到，说明你的代码里 `@mcp.tool()` 装饰器没写对，或者 Server 启动报错了（看终端日志）。
*   **手动调用 (Call Tool)**：
    *   找到 `submit_task`。
    *   在参数框里输入 JSON：`{"prompt": "测试任务", "model": "gpt-3.5-turbo"}`。
    *   点击 "Run Tool"。
    *   **观察结果**：右侧应该显示返回的 JSON，包含 `id` 和 `status: PENDING`。
    *   **观察后端**：同时看一眼你的 FastAPI 终端，应该有收到请求的日志。

**✅ 通过标准**：你能在网页上成功调用 `submit_task` 并拿到 ID，且能调用 `get_task_status` 查到结果。

---

### 🤖 第二阶段：配置 Claude Desktop (集成测试)

Inspector 测通了，说明 Server 没问题。现在要让 Claude 认识它。

#### 1. 找到配置文件
根据你的操作系统，找到 `claude_desktop_config.json` 文件。如果文件不存在，就新建一个。

*   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
*   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### 2. 修改配置
用记事本或 VS Code 打开它，填入以下内容（注意修改绝对路径）：

```json
{
  "mcpServers": {
    "my-ai-task-server": {
      "command": "uv",
      "args": [
        "run",
        "--directory","/Users/lizhao/workspace/python-learn/async-ai-task-runner",
        "run_mcp_server.py" 
      ]
    }
  }
}
```
*   **注意**：Windows 用户路径里的反斜杠 `\` 需要写成双斜杠 `\\`，例如 `C:\\Users\\Name\\Project...`。
*   **关键点**：一定要用绝对路径，因为 Claude 启动时不知道你的工作目录在哪里。

#### 3. 重启 Claude Desktop
**完全退出** Claude Desktop（不仅仅是关闭窗口，要右键图标退出），然后重新打开。

*   **检查连接**：
    *   点击 Claude 输入框右侧的“插头”图标🔌（或者回形针图标里的 MCP 菜单）。
    *   你应该能看到 `my-ai-task-server` 是绿灯状态🟢。
    *   如果显示红灯或报错，点击它查看错误日志（通常是路径写错或 Python 环境问题）。

---

### 💬 第三阶段：实战对话 (最终验收)

现在是见证奇迹的时刻。

#### 场景 1：提交任务
*   **你输入**：“请帮我生成一个关于‘量子力学’的简介，使用 gpt-4 模型。”
*   **Claude 思考**：你会看到 Claude 显示 "Running submit_task..." 的微小提示。
*   **Claude 回答**：“已为您提交任务。任务 ID 是 **15**，目前状态是 **PENDING**。需要我稍后帮您查询结果吗？”
    *   *如果 Claude 只是回答了量子力学知识而没有调用工具，说明它没理解你的意图。你可以强制说：“请使用工具提交这个生成任务”。*

#### 场景 2：查询状态 (Context 记忆)
*   **你输入**：“刚才那个任务做完了吗？”
    *   *注意：你不需要重复 ID，Claude 应该记得上下文里的 ID 是 15。*
*   **Claude 思考**：显示 "Running get_task_status(task_id=15)..."。
*   **Claude 回答**：
    *   情况 A (还在做)：“任务还在处理中 (PROCESSING)，请稍等几秒。”
    *   情况 B (做完了)：“任务已完成！以下是生成的结果：[量子力学是物理学的一个分支...]”

#### 场景 3：混合指令 (高级)
*   **你输入**：“帮我查一下 ID 10, 11, 12 这三个任务的状态。”
*   **Claude 思考**：它可能会连续调用三次 `get_task_status`，或者并行调用。
*   **Claude 回答**：“ID 10 完成了，ID 11 失败了（报错信息...），ID 12 还在做。”

---

### 🚨 常见报错与急救

1.  **Inspector 连不上**：
    *   检查端口 5173 是否被占用。
    *   检查 Python 脚本里是否有语法错误（先直接 `python run_mcp_server.py` 跑一下看看有没有报错）。

2.  **Claude 显示 "Connection Error"**：
    *   90% 是路径问题。请在终端里手动执行一下配置文件里的 `command` + `args` 拼起来的完整命令，看能不能跑通。
    *   检查 `uv` 是否在系统环境变量里。

3.  **Claude 调用了工具但报错 "Error: 500"**：
    *   这是你的 FastAPI 报错了。去检查 FastAPI 的终端日志，或者 Docker logs。

按照这个流程走，你一定能拿下 Day 4！准备好开始了吗？