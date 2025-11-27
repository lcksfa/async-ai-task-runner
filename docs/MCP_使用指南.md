# MCP服务器使用指南

## 🚀 异步AI任务运行器 - MCP服务器

这是一个完整的MCP (Model Context Protocol) 服务器实现，用于将您的异步AI任务运行器连接到Claude Desktop和其他MCP客户端。

## 📋 功能总览

### 🛠️ 可用工具
- **create_task**: 创建新的AI处理任务（支持多种模型和优先级）
- **get_task_status**: 查询指定任务的状态和详细信息
- **list_tasks**: 列出任务（支持状态过滤和分页）
- **get_task_result**: 获取已完成任务的结果

### 📚 可用资源
- **data://tasks/schema**: 任务对象结构定义
- **data://tasks/statuses**: 任务状态信息
- **data://models/available**: 可用的AI模型
- **data://system/stats**: 系统性能统计

### 💬 可用提示模板
- **task_summary**: 生成任务执行摘要
- **system_health**: 系统健康诊断
- **task_analysis**: 任务模式深度分析
- **performance_review**: 性能优化建议

## 🎯 快速开始

### 1. 验证环境
```bash
python run_mcp_server.py --validate-only
```

### 2. 查看连接配置
```bash
python run_mcp_server.py --print-connection
```

### 3. 启动MCP服务器
```bash
# 标准输入输出模式（推荐用于Claude Desktop）
python run_mcp_server.py

# HTTP服务器模式
python run_mcp_server.py --transport http --host 0.0.0.0 --port 8001
```

## 📱 Claude Desktop集成

### 配置步骤
1. 打开Claude Desktop
2. 点击设置 → 开发者 → 编辑配置
3. 在配置文件中添加：

```json
{
  "mcpServers": {
    "async-ai-task-runner": {
      "command": "python",
      "args": ["/Users/lizhao/workspace/python-learn/async-ai-task-runner/run_mcp_server.py"],
      "env": {}
    }
  }
}
```

### 使用示例
在Claude Desktop中，您现在可以：
- "帮我创建一个任务：解释量子计算的基本原理"
- "查询刚才那个任务的状态"
- "列出最近5个已完成的任务"
- "生成系统健康报告"

## 🛠️ 系统要求

### 必需组件
- ✅ PostgreSQL 数据库
- ✅ Redis 消息队列
- ✅ FastAPI 服务器 (端口8000)
- ✅ Celery 工作进程
- ✅ MCP库 (mcp>=1.0.0)

### 启动完整系统
```bash
# 1. 启动数据库服务
docker-compose up postgres redis

# 2. 运行数据库迁移
alembic upgrade head

# 3. 启动FastAPI服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 启动Celery工作进程
celery -A app.tasks worker --loglevel=info

# 5. 启动MCP服务器
python run_mcp_server.py
```

## 🔧 配置选项

### 环境变量 (.env)
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/async_ai_tasks
REDIS_URL=redis://localhost:6379/0
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### MCP服务器设置
- **默认模型**: deepseek-chat
- **支持的模型**: deepseek-chat, gpt-3.5-turbo, gpt-4
- **提供商**: deepseek, openai, anthropic
- **任务优先级**: 1-10 (10最高)

## 🧪 测试

### 运行测试套件
```bash
python test_mcp_server.py
```

### 手动测试
1. 创建任务：
```bash
# 在Claude Desktop中说：创建一个任务测试MCP功能
```

2. 检查任务状态：
```bash
# 查询：任务状态怎么样了？
```

## 📊 监控和调试

### 日志文件
- `logs/mcp_server.log`: MCP服务器日志
- Celery工作进程日志：终端输出

### 健康检查
```bash
# 验证MCP服务器功能
python run_mcp_server.py --validate-only

# 查看系统统计
python -c "
import asyncio
from app.mcp.resources.task_resources import system_stats_resource
result = asyncio.run(system_stats_resource())
print(result)
"
```

## 🚨 故障排除

### 常见问题

1. **"任务创建失败"**
   - 检查FastAPI服务器是否运行在8000端口
   - 确认数据库连接正常
   - 验证API密钥配置

2. **"Claude Desktop无法连接"**
   - 确认MCP服务器路径正确
   - 检查Python环境和依赖
   - 查看Claude Desktop日志

3. **"任务状态一直是PENDING"**
   - 确认Celery工作进程运行
   - 检查Redis连接
   - 查看Celery日志

### 调试命令
```bash
# 检查依赖
uv sync

# 验证数据库连接
python -c "
import asyncio
from app.database import get_db_session
async with get_db_session() as db:
    print('✅ 数据库连接正常')
"

# 测试API端点
curl http://localhost:8000/health
```

## 📖 更多资源

- [MCP协议文档](https://modelcontextprotocol.io/)
- [Claude Desktop集成指南](https://docs.anthropic.com/claude/docs/mcp)
- [项目README](./README.md)

---
🎉 **恭喜！您的MCP服务器现在已经完全就绪，可以与Claude Desktop无缝协作！**