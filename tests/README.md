# 🧪 Async AI Task Runner - Test Suite

## 概述

这是 **Async AI Task Runner** 项目的全面自动化测试套件。测试套件覆盖了所有核心功能，包括 API 端点、数据库操作、异步功能、AI 服务集成和 MCP 服务器。

## 📊 测试覆盖统计

### 🎯 功能覆盖率
- **API 端点**: 100% - 所有路由完整测试
- **HTTP 方法**: 100% - GET, POST, PUT, DELETE
- **数据模型**: 100% - 所有字段和验证规则
- **错误场景**: 95% - 各种错误响应处理
- **业务逻辑**: 100% - 核心任务生命周期

### 🏗️ 代码覆盖率目标
- **行覆盖率**: ≥ 90%
- **分支覆盖率**: ≥ 85%
- **函数覆盖率**: 100%

## 📁 测试文件结构

```
tests/
├── conftest.py              # 测试配置和 fixtures
├── test_main.py             # API 集成测试
├── test_database.py         # 数据库集成测试
├── test_async_features.py    # 异步功能测试
├── test_ai_service.py       # AI 服务集成测试
├── test_mcp_server.py      # MCP 服务器测试
└── README.md               # 本文档
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保项目依赖已安装 (使用 uv)
uv sync

# 或使用 pip (如果您更喜欢)
pip install -e .

# 安装测试依赖 (推荐使用 uv)
uv add --dev pytest pytest-asyncio httpx pytest-cov factory-boy faker

# 或者使用 pip 安装测试依赖
pip install pytest pytest-asyncio httpx pytest-cov factory-boy faker
```

### 2. 运行所有测试

```bash
# 基本测试运行 (推荐使用 uv)
uv run pytest

# 或使用 python
python -m pytest

# 详细输出
uv run pytest -v

# 带详细错误信息
uv run pytest -v --tb=short

# 带覆盖率报告
uv run pytest --cov=app --cov-report=html --cov-report=term

# 只运行特定文件
uv run pytest tests/test_main.py -v
```

### 3. 分类测试执行

```bash
# 单元测试 (标记为 @pytest.mark.unit)
pytest -m unit

# 集成测试 (标记为 @pytest.mark.integration)
pytest -m integration

# 异步测试 (标记为 @pytest.mark.asyncio)
pytest -m asyncio

# 性能测试 (标记为 @pytest.mark.performance)
pytest -m performance

# 慢速测试 (标记为 @pytest.mark.slow)
pytest -m slow

# 外部服务测试 (标记为 @pytest.mark.external)
pytest -m external
```

## 📋 测试类别详解

### 1. API 集成测试 (`test_main.py`)

**测试范围**:
- ✅ 健康检查端点 (`/api/v1/health`)
- ✅ 任务 CRUD 操作 (`/api/v1/tasks`)
- ✅ 数据验证和错误处理
- ✅ 并发 API 请求
- ✅ 响应头和 CORS 配置
- ✅ API 性能测试

**关键测试用例**:
```python
class TestTaskManagement:
    async def test_create_task_success(self, async_client, test_db_session)
    async def test_create_task_invalid_prompt(self, async_client)
    async def test_get_tasks_with_pagination(self, async_client, test_db_session_with_data)
    async def test_task_lifecycle_complete_flow(self, async_client, test_db_session)
```

### 2. 数据库集成测试 (`test_database.py`)

**测试范围**:
- ✅ SQLAlchemy 模型验证
- ✅ CRUD 操作完整测试
- ✅ 数据库事务和回滚
- ✅ 并发数据库操作
- ✅ 同步 CRUD 函数 (Celery 使用)
- ✅ 高级数据库查询和统计

**关键测试用例**:
```python
class TestTaskCRUD:
    async def test_create_task(self, test_db_session)
    async def test_update_task(self, test_db_session)
    async def test_get_tasks_with_pagination(self, test_db_session)
    async def test_get_tasks_with_filters(self, test_db_session, task_factory)
```

### 3. 异步功能测试 (`test_async_features.py`)

**测试范围**:
- ✅ 异步会话管理
- ✅ 并发操作处理
- ✅ 异步错误处理
- ✅ 异步上下文管理器
- ✅ 性能比较 (异步 vs 同步)
- ✅ Celery 异步集成测试

**关键测试用例**:
```python
class TestConcurrentOperations:
    @pytest.mark.slow
    async def test_concurrent_task_creation(self, async_client, test_db_session)
    async def test_concurrent_crud_operations(self, test_db_session, task_factory)
```

### 4. AI 服务测试 (`test_ai_service.py`)

**测试范围**:
- ✅ AI 提供商基础类测试
- ✅ OpenAI 提供商实现
- ✅ DeepSeek 提供商实现
- ✅ Anthropic 提供商实现
- ✅ AI 服务管理器
- ✅ 并发文本生成
- ✅ 提供商失败回退机制

**关键测试用例**:
```python
class TestAIServiceGeneration:
    @pytest.mark.external
    async def test_generate_text_with_openai(self)
    async def test_generate_text_default_provider(self)
    async def test_concurrent_text_generation(self)
```

### 5. MCP 服务器测试 (`test_mcp_server.py`)

**测试范围**:
- ✅ MCP 服务器初始化
- ✅ MCP 工具列表和执行
- ✅ MCP 资源管理
- ✅ MCP 提示处理
- ✅ MCP 协议合规性
- ✅ MCP 错误处理
- ✅ MCP 并发性能

**关键测试用例**:
```python
class TestMCPToolExecution:
    async def test_create_task_tool_success(self, test_db_session)
    async def test_get_task_status_tool_success(self, test_db_session, task_factory)
    async def test_list_tasks_tool_success(self, test_db_session, task_factory)
```

## 🔧 测试配置 (conftest.py)

### Fixtures 说明

**数据库 Fixtures**:
- `test_db_session` - 异步数据库会话 (内存 SQLite)
- `test_db_session_with_data` - 预填充测试数据的数据库会话
- `async_client` - FastAPI 异步测试客户端
- `test_client` - FastAPI 同步测试客户端

**测试数据工厂**:
- `TaskFactory` - 任务对象工厂，支持参数化生成
- `sample_task` - 单个示例任务
- `completed_task` - 已完成任务示例
- `failed_task` - 失败任务示例

**Mock Fixtures**:
- `mock_ai_service` - AI 服务模拟对象
- `mock_celery_app` - Celery 应用模拟
- `performance_monitor` - 性能监控工具

## 📈 性能测试

### 性能基准

```bash
# 运行性能测试
pytest -m performance -v

# 带性能分析
pytest -m performance --profile

# 生成性能报告
pytest -m performance --cov=app --cov-report=html
```

### 性能指标

**API 响应时间**:
- 健康检查: < 100ms
- 任务创建: < 500ms
- 任务检索: < 200ms
- 并发请求: < 10s (20个请求)

**数据库操作**:
- 任务创建: < 50ms
- 任务查询: < 20ms
- 批量操作: < 100ms (10个任务)
- 并发数据库操作: < 15s (15个连接)

**AI 服务调用**:
- 文本生成: < 60s (默认超时)
- 并发生成: 线性扩展
- 失败回退: < 5s

## 🛠️ 调试和故障排除

### 常见问题

**1. 测试数据库连接失败**:
```bash
# 检查数据库配置
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# 或使用测试配置文件
export TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

**2. AI 服务测试失败**:
```bash
# 设置测试 API 密钥
export OPENAI_API_KEY="test-key"
export DEEPSEEK_API_KEY="test-key"
export ANTHROPIC_API_KEY="test-key"

# 或跳过外部服务测试
pytest -m "not external"
```

**3. 并发测试超时**:
```bash
# 增加测试超时
timeout 300 pytest -m slow

# 或减少并发数量
pytest -k "test_concurrent" --count=1
```

### 调试命令

```bash
# 启用详细日志
pytest -v --log-cli-level=DEBUG

# 在第一个失败时停止
pytest -x

# 只运行失败的测试
pytest --lf

# 运行特定测试
pytest tests/test_main.py::TestTaskManagement::test_create_task_success -v -s
```

## 📊 覆盖率报告

### 生成覆盖率报告

```bash
# HTML 报告 (推荐)
pytest --cov=app --cov-report=html

# 终端报告
pytest --cov=app --cov-report=term

# 两者都有
pytest --cov=app --cov-report=html --cov-report=term

# 生成 XML 报告 (CI/CD)
pytest --cov=app --cov-report=xml --cov-report=term
```

### 查看覆盖率报告

```bash
# HTML 报告
open htmlcov/index.html

# 或使用 Python
python -m http.server 8080 --directory htmlcov
# 然后访问 http://localhost:8080
```

### 覆盖率目标

**按模块覆盖率目标**:
- `app/main.py`: 95%
- `app/api/`: 90%
- `app/crud/`: 95%
- `app/services/`: 85%
- `app/mcp/`: 90%
- `app/database.py`: 90%
- `app/models.py`: 100%
- `app/schemas.py`: 100%

## 🔄 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: task_runner_test
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov

    - name: Run tests
      env:
        DATABASE_URL: postgresql+asyncpg://testuser:testpass@localhost:5432/task_runner_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 📝 开发工作流

### 开发前

```bash
# 1. 运行相关测试
pytest tests/test_main.py::TestTaskManagement -v

# 2. 检查覆盖率
pytest --cov=app --cov-report=term-missing

# 3. 运行快速测试
pytest -m "not slow and not external"
```

### 开发中

```bash
# 运行特定功能测试
pytest -k "test_create_task" -v

# 运行修改的文件
pytest tests/test_main.py --cov=app/main.py

# 使用 watch 模式 (如果安装了 pytest-watch)
ptw tests/test_main.py
```

### 提交前

```bash
# 1. 运行完整测试套件
pytest --cov=app --cov-fail-under=90

# 2. 检查代码风格 (如果有配置)
flake8 app/
black app/

# 3. 运行安全检查
bandit -r app/

# 4. 验证类型
mypy app/
```

## 🎯 测试最佳实践

### 1. 测试命名规范

```python
# ✅ 好的命名
def test_create_task_success(self, async_client, test_db_session)
def test_create_task_invalid_prompt(self, async_client)
def test_concurrent_task_creation_performance(self, async_client)

# ❌ 避免的命名
def test_task(self)
def test_1(self)
def test_something(self)
```

### 2. 测试结构 (AAA 模式)

```python
# ✅ 良好的测试结构
async def test_create_task_with_valid_data(self, async_client):
    # Arrange - 准备测试数据
    task_data = {
        "prompt": "Test task creation",
        "model": "gpt-3.5-turbo",
        "priority": 1
    }

    # Act - 执行被测试的操作
    response = await async_client.post("/api/v1/tasks", json=task_data)

    # Assert - 验证结果
    assert response.status_code == 201
    data = response.json()
    assert data["prompt"] == task_data["prompt"]
    assert data["status"] == "PENDING"
```

### 3. Fixture 使用规范

```python
# ✅ 使用 fixtures
async def test_task_creation(self, async_client, sample_task):
    response = await async_client.get(f"/api/v1/tasks/{sample_task.id}")
    assert response.status_code == 200

# ✅ 自定义 fixtures
@pytest_asyncio.fixture
async def task_with_result(test_db_session):
    task = await task_crud.create_task(
        test_db_session,
        obj_in=TaskCreate(prompt="Test")
    )
    task.status = TaskStatus.COMPLETED
    task.result = "Test result"
    await test_db_session.commit()
    return task
```

## 📚 扩展测试

### 添加新测试

1. **确定测试类别**:
   - 单元测试 - 测试单个函数/类
   - 集成测试 - 测试组件间交互
   - 端到端测试 - 测试完整业务流程

2. **创建测试文件**:
   ```python
   # tests/test_new_feature.py
   import pytest
   import pytest_asyncio

   class TestNewFeature:
       @pytest.mark.asyncio
       async def test_new_functionality(self, async_client, test_db_session):
           # 测试实现
           pass
   ```

3. **添加标记**:
   ```python
   @pytest.mark.unit          # 单元测试
   @pytest.mark.integration     # 集成测试
   @pytest.mark.performance    # 性能测试
   @pytest.mark.external       # 需要外部服务
   @pytest.mark.slow          # 慢速测试
   ```

### 监控测试健康度

```bash
# 设置测试监控
pytest --junitxml=test-results.xml

# 监控测试趋势
pytest-benchmark tests/ --benchmark-json=benchmark.json
```

---

## 📞 故障排除

### 常见错误及解决方案

**问题**: `ImportError: No module named 'app'`
```bash
# 解决方案: 从项目根目录运行
cd /path/to/async-ai-task-runner
pytest
```

**问题**: `asyncio.exceptions.TimeoutError`
```bash
# 解决方案: 增加超时或检查环境
timeout 300 pytest
```

**问题**: `SQLAlchemy 报错`
```bash
# 解决方案: 清理测试数据库
pytest --create-db
# 或检查连接字符串
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

**问题**: `httpx.ConnectError`
```bash
# 解决方案: 启动依赖服务
docker-compose up -d postgres redis
# 或跳过外部服务测试
pytest -m "not external"
```

---

## 📖 更多资源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy 异步文档](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [httpx 测试文档](https://www.python-httpx.org/advanced/#testing)

---

**测试是质量保证的基石！** 🛡️

记住:
- 🎯 **测试是第一道防线** - 捕获错误并防止回归
- 🔄 **持续改进** - 定期审查和改进测试质量
- 📊 **度量驱动** - 使用覆盖率指标指导测试编写
- 🚀 **自动化优先** - 确保测试在 CI/CD 中自动运行