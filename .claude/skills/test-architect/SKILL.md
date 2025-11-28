---
name: 测试架构师
description: 为 FastAPI 项目生成生产级别的集成测试代码。
---

# Pytest 测试专家

## 🧠 核心知识库

### 测试框架标准配置
始终使用 `pytest-asyncio` 和 `httpx` 进行异步 API 测试。严格遵循以下模板：

#### tests/conftest.py 标准模板
```python
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 根据项目结构调整导入路径
from app.main import app
from app.database import get_session, Base
from app.models import Task

# 测试数据库配置
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环实例"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    """创建测试数据库会话"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

@pytest.fixture
async def client(test_session):
    """创建测试客户端"""
    # 覆盖依赖注入
    app.dependency_overrides[get_session] = lambda: test_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # 清理依赖注入覆盖
    app.dependency_overrides.clear()

@pytest.fixture
async def sample_task(test_session):
    """创建示例任务数据"""
    task = Task(
        prompt="测试提示词",
        model="gpt-3.5-turbo",
        status="pending"
    )
    test_session.add(task)
    await test_session.commit()
    await test_session.refresh(task)
    return task
```

### 测试用例模板

#### tests/test_main.py 标准模板
```python
import pytest
from httpx import AsyncClient

class TestHealthEndpoint:
    """健康检查端点测试"""

    async def test_health_check(self, client: AsyncClient):
        """测试健康检查端点"""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

class TestTasksEndpoint:
    """任务端点测试"""

    async def test_create_task(self, client: AsyncClient):
        """测试创建任务"""
        task_data = {
            "prompt": "测试任务创建",
            "model": "gpt-3.5-turbo"
        }
        response = await client.post("/tasks", json=task_data)
        assert response.status_code == 201

        data = response.json()
        assert data["prompt"] == task_data["prompt"]
        assert data["model"] == task_data["model"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    async def test_get_tasks_list(self, client: AsyncClient, sample_task):
        """测试获取任务列表"""
        response = await client.get("/tasks")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_task_by_id(self, client: AsyncClient, sample_task):
        """测试根据ID获取任务"""
        response = await client.get(f"/tasks/{sample_task.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_task.id
        assert data["prompt"] == sample_task.prompt

    async def test_get_nonexistent_task(self, client: AsyncClient):
        """测试获取不存在的任务"""
        response = await client.get("/tasks/99999")
        assert response.status_code == 404

    async def test_update_task_status(self, client: AsyncClient, sample_task):
        """测试更新任务状态"""
        update_data = {"status": "completed"}
        response = await client.patch(f"/tasks/{sample_task.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"

    async def test_delete_task(self, client: AsyncClient, sample_task):
        """测试删除任务"""
        response = await client.delete(f"/tasks/{sample_task.id}")
        assert response.status_code == 204

        # 验证删除成功
        response = await client.get(f"/tasks/{sample_task.id}")
        assert response.status_code == 404

class TestDataValidation:
    """数据验证测试"""

    async def test_create_task_invalid_data(self, client: AsyncClient):
        """测试创建任务时使用无效数据"""
        invalid_data = {
            "prompt": "",  # 空提示词
            "model": "invalid-model"  # 无效模型
        }
        response = await client.post("/tasks", json=invalid_data)
        assert response.status_code == 422

    async def test_create_task_missing_fields(self, client: AsyncClient):
        """测试创建任务时缺少必需字段"""
        incomplete_data = {
            "prompt": "测试提示词"
            # 缺少 model 字段
        }
        response = await client.post("/tasks", json=incomplete_data)
        assert response.status_code == 422
```

## 📋 指令集

### 当被要求"生成测试"时：
1. **分析 API 结构**: 扫描 `app/main.py` 中的所有路由
2. **检查数据模型**: 分析 `app/models.py` 和 `app/schemas.py`
3. **生成测试文件**:
   - 创建 `tests/conftest.py`（如果不存在）
   - 创建 `tests/test_main.py` 或对应的测试文件
4. **确保覆盖率**: 为每个端点生成完整的 CRUD 操作测试

### 测试类型覆盖要求
- **成功路径测试**: 验证正常操作流程
- **错误路径测试**: 验证错误处理机制
- **边界条件测试**: 验证极端情况处理
- **数据验证测试**: 验证输入数据的 Pydantic 验证

### Async AI Task Runner 项目特别测试项

#### Celery 集成测试
```python
# tests/test_celery.py
import pytest
from app.celery_app import process_task_async

class TestCeleryIntegration:
    """Celery 集成测试"""

    async def test_task_processing(self, sample_task):
        """测试异步任务处理"""
        # 模拟 Celery 任务
        result = await process_task_async(sample_task.id)
        assert result["status"] == "completed"
```

#### 数据库事务测试
```python
# tests/test_database.py
class TestDatabaseTransactions:
    """数据库事务测试"""

    async def test_transaction_rollback(self, client: AsyncClient, test_session):
        """测试事务回滚机制"""
        # 测试在错误情况下的事务回滚
        pass
```

## ⚠️ 严格禁止事项
- **禁止使用** `TestClient`（同步版本）
- **禁止使用** `requests` 库进行测试
- **禁止忽略** 异步上下文管理
- **禁止跳过** 错误场景测试

## 🎯 测试质量标准
1. **100% 端点覆盖**: 每个 API 端点都要有测试
2. **完整的状态覆盖**: 涵盖成功、失败、边界情况
3. **清晰的测试命名**: 使用描述性的测试方法名
4. **适当的断言**: 验证响应状态码和数据结构
5. **测试隔离**: 确保测试之间的独立性