# Async AI Task Runner

一个基于FastAPI的异步AI任务处理平台，按照5天学习计划从基础构建到生产就绪。

## 🚀 快速开始

### 环境要求
- Python 3.12+
- uv (推荐的包管理器)

### 安装依赖
```bash
# 如果使用uv
uv sync

# 或使用pip
pip install -e .
```

### 运行开发服务器
```bash
# 使用uvicorn直接运行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用开发脚本
python scripts/development/start_dev.py
```

### 访问API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 学习计划

### Day 1: FastAPI + SQL 基础 ✅
- [x] FastAPI路由和依赖注入
- [x] Pydantic数据验证
- [x] `/health`健康检查接口
- [x] `/tasks` POST接口创建任务
- [x] 异步SQLAlchemy配置

### Day 2: Celery + Redis 异步任务
- [ ] Celery后台任务处理
- [ ] Redis消息队列配置
- [ ] 任务状态管理

### Day 3: Docker容器化
- [ ] Dockerfile编写
- [ ] Docker Compose编排
- [ ] 环境变量管理

### Day 4: MCP服务器
- [ ] Model Context Protocol实现
- [ ] AI客户端集成

### Day 5: 测试与文档
- [ ] pytest测试框架
- [ ] 集成测试
- [ ] 生产就绪配置

## 🔧 API接口

### Health Check
```
GET /api/v1/health
```

### Tasks
```
POST /api/v1/tasks     # 创建新任务
GET /api/v1/tasks      # 获取任务列表
GET /api/v1/tasks/{id} # 获取特定任务
```

## 整体架构
async-ai-task-runner/
├── app/                     # 主应用目录
│   ├── api/                # API层 (Day 1)
│   │   ├── v1/endpoints/   # API路由端点
│   │   └── deps/          # 依赖注入
│   ├── core/              # 核心配置和工具
│   ├── crud/              # 数据库操作层 (Day 1)
│   ├── worker/            # Celery异步任务 (Day 2)
│   │   ├── tasks/         # 具体任务定义
│   │   └── celery_app/    # Celery应用配置
│   └── mcp/               # MCP服务器 (Day 4)
│       ├── tools/         # MCP工具
│       ├── resources/     # MCP资源
│       └── prompts/       # MCP提示词
├── alembic/               # 数据库迁移 (Day 1)
│   └── versions/          # 迁移版本文件
├── tests/                 # 测试目录 (Day 5)
│   ├── unit/             # 单元测试
│   ├── integration/      # 集成测试
│   └── conftest/         # pytest配置
├── docker/               # 容器化配置 (Day 3)
│   ├── postgres/         # PostgreSQL配置
│   └── redis/           # Redis配置
├── docs/                 # 项目文档 (Day 5)
│   ├── api/             # API文档
│   ├── deployment/      # 部署文档
│   └── architecture/    # 架构文档
├── scripts/              # 脚本目录
│   ├── setup/           # 环境设置脚本
│   ├── development/     # 开发脚本
│   └── deployment/      # 部署脚本
├── config/              # 配置文件目录
├── .env.example         # 环境变量模板 (Day 3)
└── alembic/            # 数据库迁移工具目录


## 📅 各天数目录功能：
Day 1 - FastAPI + SQL: app/api/, app/crud/, app/core/, alembic/
API路由和依赖注入结构
数据库操作层
核心配置管理
Alembic数据库迁移

Day 2 - Celery + Redis: app/worker/
Celery应用配置
异步任务定义
消息队列集成

Day 3 - Docker配置: docker/, config/, .env.example
PostgreSQL和Redis容器配置
环境变量管理
部署脚本

Day 4 - MCP服务器: app/mcp/
MCP工具、资源和提示词
AI客户端协议集成

Day 5 - 测试与文档: tests/, docs/
单元测试和集成测试框架
API文档和架构文档
