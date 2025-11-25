"""
使用 pytest 进行 API 自动化测试

安装 pytest: uv add pytest pytest-asyncio httpx

运行测试:
    uv run pytest test_api_pytest.py -v
    uv run pytest test_api_pytest.py -v --tb=short
    uv run pytest test_api_pytest.py::TestTasksAPI::test_health -v
"""

import pytest
import httpx
from typing import Dict, Any, List
import json
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class TestHealthAPI:
    """健康检查 API 测试"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查接口"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health")

            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["app_name"] == "Async AI Task Runner"
            assert data["version"] == "0.1.0"
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """测试根端点"""
        async with httpx.AsyncClient() as client:
            response = await client.get(BASE_URL)

            assert response.status_code == 200

            data = response.json()
            assert "message" in data
            assert "docs" in data
            assert "redoc" in data
            assert "api" in data

class TestTasksAPI:
    """任务管理 API 测试"""

    @pytest.fixture
    async def client(self):
        """创建 HTTP 客户端"""
        async with httpx.AsyncClient() as client:
            yield client

    @pytest.fixture
    async def sample_task_data(self):
        """示例任务数据"""
        return {
            "prompt": "测试任务提示语",
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

    @pytest.mark.asyncio
    async def test_create_task_success(self, client, sample_task_data):
        """测试成功创建任务"""
        response = await client.post(
            f"{API_BASE}/tasks",
            json=sample_task_data
        )

        assert response.status_code == 201

        data = response.json()
        assert data["prompt"] == sample_task_data["prompt"]
        assert data["model"] == sample_task_data["model"]
        assert data["priority"] == sample_task_data["priority"]
        assert data["status"] == "PENDING"
        assert data["id"] is not None
        assert data["created_at"] is not None
        assert data["result"] is None

    @pytest.mark.asyncio
    async def test_create_task_with_defaults(self, client):
        """测试创建任务时使用默认值"""
        task_data = {
            "prompt": "简单测试任务"
        }

        response = await client.post(
            f"{API_BASE}/tasks",
            json=task_data
        )

        assert response.status_code == 201

        data = response.json()
        assert data["prompt"] == task_data["prompt"]
        assert data["model"] == "gpt-3.5-turbo"  # 默认值
        assert data["priority"] == 1  # 默认值

    @pytest.mark.asyncio
    async def test_create_task_invalid_data(self, client):
        """测试创建任务时数据验证"""
        # 测试空提示语
        invalid_data = {
            "prompt": "",
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        response = await client.post(
            f"{API_BASE}/tasks",
            json=invalid_data
        )

        assert response.status_code == 422  # 验证错误

    @pytest.mark.asyncio
    async def test_create_task_invalid_priority(self, client):
        """测试无效的优先级"""
        invalid_data = {
            "prompt": "测试任务",
            "model": "gpt-3.5-turbo",
            "priority": 15  # 超出范围 (1-10)
        }

        response = await client.post(
            f"{API_BASE}/tasks",
            json=invalid_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_tasks_empty(self, client):
        """测试获取空任务列表（需要清空数据库）"""
        # 注意：这个测试需要在空数据库环境下运行
        response = await client.get(f"{API_BASE}/tasks")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_tasks_with_pagination(self, client, sample_task_data):
        """测试分页获取任务"""
        # 创建几个任务
        task_ids = []
        for i in range(3):
            task_data = {
                "prompt": f"分页测试任务 {i+1}",
                "model": "gpt-3.5-turbo",
                "priority": i+1
            }
            response = await client.post(f"{API_BASE}/tasks", json=task_data)
            assert response.status_code == 201
            task_ids.append(response.json()["id"])

        # 测试分页
        response = await client.get(f"{API_BASE}/tasks?skip=0&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

        # 测试偏移
        response = await client.get(f"{API_BASE}/tasks?skip=2&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_single_task_success(self, client, sample_task_data):
        """测试成功获取单个任务"""
        # 先创建一个任务
        create_response = await client.post(
            f"{API_BASE}/tasks",
            json=sample_task_data
        )
        assert create_response.status_code == 201

        task_id = create_response.json()["id"]

        # 获取任务
        response = await client.get(f"{API_BASE}/tasks/{task_id}")

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == task_id
        assert data["prompt"] == sample_task_data["prompt"]

    @pytest.mark.asyncio
    async def test_get_single_task_not_found(self, client):
        """测试获取不存在的任务"""
        response = await client.get(f"{API_BASE}/tasks/99999")

        assert response.status_code == 404

        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_task_workflow(self, client):
        """测试完整的任务工作流"""
        # 1. 创建任务
        task_data = {
            "prompt": "完整工作流测试",
            "model": "gpt-4",
            "priority": 5
        }

        create_response = await client.post(f"{API_BASE}/tasks", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 2. 获取单个任务
        get_response = await client.get(f"{API_BASE}/tasks/{task_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == task_id

        # 3. 获取任务列表
        list_response = await client.get(f"{API_BASE}/tasks")
        assert list_response.status_code == 200

        tasks = list_response.json()
        task_ids = [task["id"] for task in tasks]
        assert task_id in task_ids

class TestAPIPerformance:
    """API 性能测试"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求"""
        import asyncio

        async def create_task(index):
            task_data = {
                "prompt": f"并发测试任务 {index}",
                "model": "gpt-3.5-turbo",
                "priority": 1
            }

            async with httpx.AsyncClient() as client:
                start_time = datetime.now()
                response = await client.post(f"{API_BASE}/tasks", json=task_data)
                end_time = datetime.now()

                return response.status_code, (end_time - start_time).total_seconds()

        # 并发创建 5 个任务
        tasks = [create_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # 验证所有请求都成功
        for status_code, response_time in results:
            assert status_code == 201
            assert response_time < 5.0  # 响应时间应少于 5 秒

    @pytest.mark.asyncio
    async def test_large_prompt(self):
        """测试长提示语"""
        long_prompt = "这是一个很长的提示语，" * 100  # 创建一个长提示语

        task_data = {
            "prompt": long_prompt,
            "model": "gpt-3.5-turbo",
            "priority": 1
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE}/tasks", json=task_data)

            # 根据模型验证长度限制（当前限制是1000字符）
            if len(long_prompt) > 1000:
                assert response.status_code == 422
            else:
                assert response.status_code == 201

# 测试配置和工具函数
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

def pytest_configure(config):
    """pytest 配置"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )

# 测试报告生成
def pytest_html_report_title(report):
    """自定义 HTML 报告标题"""
    report.title = "Async AI Task Runner API 测试报告"

if __name__ == "__main__":
    # 可以直接运行，但建议使用 pytest
    import asyncio

    async def run_basic_test():
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health")
            print(f"Health check: {response.status_code}")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    asyncio.run(run_basic_test())