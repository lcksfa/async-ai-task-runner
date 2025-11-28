---
description: 生成自动化测试代码
---

# 🧪 自动化测试生成

## 角色激活
立即作为 **SDET Bot** (定义在 `agents/sdet.md` 中) 开始工作。

## 🎯 测试生成任务

### 主要目标
为 Async AI Task Runner 项目生成全面的自动化测试套件，确保代码质量和功能完整性。

### 测试策略范围
1. **API 集成测试** - FastAPI 端点的完整测试
2. **数据库集成测试** - SQLAlchemy 异步 ORM 测试
3. **异步功能测试** - 异步操作和并发测试
4. **数据验证测试** - Pydantic 模式验证测试

## 🔧 项目分析要求

### 第一步：API 端点分析
扫描并分析 `app/main.py` 中的所有路由：

```python
# 需要识别的端点模式示例
@app.get("/health")                    # 健康检查
@app.post("/tasks")                    # 创建任务
@app.get("/tasks")                     # 获取任务列表
@app.get("/tasks/{task_id}")           # 获取单个任务
@app.patch("/tasks/{task_id}")         # 更新任务状态
@app.delete("/tasks/{task_id}")        # 删除任务
```

### 第二步：数据模型分析
检查 `app/models.py` 和 `app/schemas.py`：

#### 数据库模型 (SQLAlchemy)
```python
# Task 模型结构分析
class Task(Base):
    id: int (Primary Key)
    prompt: str (必需)
    model: str (必需)
    status: Enum (PENDING, PROCESSING, COMPLETED, FAILED)
    result: Optional[str]
    created_at: DateTime
    updated_at: DateTime
```

#### API 模式 (Pydantic)
```python
# 请求模式分析
class TaskCreate(BaseModel):
    prompt: str
    model: str

# 响应模式分析
class TaskResponse(BaseModel):
    id: int
    prompt: str
    model: str
    status: str
    result: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### 第三步：数据库配置分析
检查 `app/database.py` 和相关的数据库配置：

- 异步引擎配置
- 会话管理方式
- 依赖注入实现
- 连接池设置

## 🧪 测试文件生成规范

### 必须生成的文件

#### 1. tests/conftest.py
生成标准的测试配置，包含：
- 异步测试事件循环
- 测试数据库引擎配置
- 测试客户端 fixture
- 数据库会话 fixture
- 示例数据 fixture

#### 2. tests/test_main.py
生成完整的 API 端点测试：
- 健康检查端点测试
- 任务 CRUD 操作测试
- 错误场景和边界条件测试
- 数据验证测试

#### 3. tests/test_database.py
生成数据库集成测试：
- 模型创建和验证测试
- 事务处理测试
- 并发操作测试
- 数据完整性测试

#### 4. tests/test_async_features.py (如果需要)
生成异步功能专项测试：
- 并发请求处理测试
- 异步会话管理测试
- 性能和响应时间测试

### Async AI Task Runner 专项测试

#### 核心业务流程测试
```python
class TestAsyncAITaskRunner:
    """AI 任务处理核心流程测试"""

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self, client: AsyncClient, test_session):
        """测试完整的任务生命周期"""
        # 1. 创建任务
        task_data = {
            "prompt": "测试提示词",
            "model": "gpt-3.5-turbo"
        }
        response = await client.post("/tasks", json=task_data)
        assert response.status_code == 201

        task = response.json()
        assert task["status"] == "pending"

        # 2. 获取任务详情
        response = await client.get(f"/tasks/{task['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

        # 3. 更新任务状态 (模拟处理完成)
        update_data = {"status": "completed", "result": "测试结果"}
        response = await client.patch(f"/tasks/{task['id']}", json=update_data)
        assert response.status_code == 200

        updated_task = response.json()
        assert updated_task["status"] == "completed"
        assert updated_task["result"] == "测试结果"

    @pytest.mark.asyncio
    async def test_concurrent_task_creation(self, client: AsyncClient, test_session):
        """测试并发任务创建"""
        import asyncio

        task_data = {
            "prompt": "并发测试任务",
            "model": "gpt-3.5-turbo"
        }

        # 创建多个并发请求
        tasks = [
            client.post("/tasks", json=task_data)
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 201

        # 验证数据库中所有任务都被创建
        response = await client.get("/tasks")
        tasks_list = response.json()
        assert len(tasks_list) >= 5
```

#### 数据验证和错误处理测试
```python
class TestDataValidation:
    """数据验证和错误处理测试"""

    @pytest.mark.asyncio
    async def test_create_task_empty_prompt(self, client: AsyncClient):
        """测试创建任务时空提示词的验证"""
        invalid_data = {
            "prompt": "",
            "model": "gpt-3.5-turbo"
        }
        response = await client.post("/tasks", json=invalid_data)
        assert response.status_code == 422

        error_detail = response.json()["detail"][0]
        assert error_detail["type"] == "value_error"
        assert "prompt" in str(error_detail["msg"]).lower()

    @pytest.mark.asyncio
    async def test_create_task_invalid_model(self, client: AsyncClient):
        """测试创建任务时无效模型的验证"""
        invalid_data = {
            "prompt": "测试提示词",
            "model": "invalid-model-name"
        }
        response = await client.post("/tasks", json=invalid_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, client: AsyncClient):
        """测试获取不存在的任务"""
        response = await client.get("/tasks/99999")
        assert response.status_code == 404

        error = response.json()
        assert "not found" in error["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_nonexistent_task(self, client: AsyncClient):
        """测试更新不存在的任务"""
        update_data = {"status": "completed"}
        response = await client.patch("/tasks/99999", json=update_data)
        assert response.status_code == 404
```

## 📊 测试覆盖率要求

### 功能覆盖率目标
- **API 端点**: 100% - 所有路由必须测试
- **HTTP 方法**: 100% - GET, POST, PATCH, DELETE
- **数据模型**: 100% - 所有字段和验证
- **错误场景**: 95% - 各种错误响应
- **业务逻辑**: 100% - 核心功能流程

### 代码覆盖率目标
- **行覆盖率**: ≥ 90%
- **分支覆盖率**: ≥ 85%
- **函数覆盖率**: 100%

## 🔧 测试执行和验证

### 运行测试的命令
```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx pytest-cov factory-boy

# 运行所有测试
pytest -v

# 运行覆盖率测试
pytest --cov=app --cov-report=html --cov-report=term

# 运行特定测试类
pytest tests/test_main.py::TestTaskManagement -v

# 运行特定测试方法
pytest tests/test_main.py::TestTaskManagement::test_create_task_success -v
```

### 验证测试质量
- 所有测试必须独立运行
- 测试数据必须隔离
- 异步测试必须正确配置
- Mock 对象使用合理

## 📋 预期输出格式

```markdown
# 🧪 SDET 测试生成报告

## 📊 项目分析结果
- **API 端点**: [数量] 个
- **数据模型**: [数量] 个 (Task)
- **HTTP 方法**: GET, POST, PATCH, DELETE
- **测试覆盖率目标**: 90%+ 行覆盖率

## 🎯 生成的测试文件
- ✅ `tests/conftest.py` - 测试配置和 fixtures
- ✅ `tests/test_main.py` - API 集成测试
- ✅ `tests/test_database.py` - 数据库集成测试
- ✅ `tests/test_async_features.py` - 异步功能测试

## 🚀 执行测试

### 安装依赖
```bash
pip install pytest pytest-asyncio httpx pytest-cov factory-boy
```

### 运行所有测试
```bash
pytest -v --cov=app --cov-report=html
```

### 检查测试结果
```bash
# 查看覆盖率报告
open htmlcov/index.html

# 查看详细测试结果
pytest -v --tb=short
```

## 📈 测试统计
- **总测试数**: [数量] 个
- **API 测试**: [数量] 个
- **数据库测试**: [数量] 个
- **异步功能测试**: [数量] 个
- **预期覆盖率**: 90%+

## 🔧 测试特性
- ✅ 完整的 CRUD 操作测试
- ✅ 数据验证和错误处理测试
- ✅ 异步操作和并发测试
- ✅ 数据库事务和会话测试
- ✅ 业务流程端到端测试

## 🎯 测试覆盖场景
### 成功路径测试
- [x] 健康检查端点
- [x] 创建任务
- [x] 获取任务列表
- [x] 获取单个任务
- [x] 更新任务状态
- [x] 删除任务

### 错误场景测试
- [x] 无效数据验证
- [x] 不存在资源访问
- [x] 数据库约束违反
- [x] 异常处理机制

### 并发和异步测试
- [x] 并发任务创建
- [x] 异步会话管理
- [x] 数据库事务隔离
- [x] 异步操作正确性

## 🔍 下一步建议
- [ ] 在 CI/CD 中集成自动化测试
- [ ] 添加性能和负载测试
- [ ] 实现测试数据工厂模式
- [ ] 添加测试报告和监控
- [ ] 考虑添加契约测试

## 🎉 测试质量保证
- **独立性**: 每个测试都可以独立运行
- **隔离性**: 测试之间不共享状态
- **完整性**: 覆盖所有业务场景
- **可维护性**: 清晰的测试结构和命名
```

## ⚡ 快速启动命令

如果用户想要立即开始测试：

```bash
# 1. 创建测试目录
mkdir -p tests

# 2. 安装测试依赖
pip install pytest pytest-asyncio httpx pytest-cov

# 3. 运行生成的测试
pytest -v --cov=app
```

## 🎯 成功标准
测试生成成功的标准：
- 所有 API 端点都有对应的测试
- 测试覆盖正常和异常情况
- 异步测试正确配置和执行
- 提供清晰的测试执行指导
- 确保测试的质量和可维护性

记住：**质量是构建出来的，不是测试出来的！你的任务是为每一行代码提供全面、可靠的测试保障。**