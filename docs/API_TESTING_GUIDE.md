# API 接口测试指南

本文档提供了 Async AI Task Runner API 的完整测试指南。

## 📋 API 端点概览

### 基础信息
- **Base URL**: `http://localhost:8000`
- **API 版本**: `/api/v1`
- **认证**: 暂无（Day 1 阶段）

### 可用端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 根端点，返回应用信息 |
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/tasks` | GET | 获取任务列表 |
| `/api/v1/tasks` | POST | 创建新任务 |
| `/api/v1/tasks/{task_id}` | GET | 获取指定任务 |

## 🚀 测试方法

### 1. 浏览器测试（推荐新手）

访问以下地址进行交互式测试：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 2. curl 命令行测试

#### 健康检查
```bash
# 基础健康检查
curl http://localhost:8000/api/v1/health

# 格式化输出
curl http://localhost:8000/api/v1/health | jq .
```

#### 创建任务
```bash
# 创建基础任务
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "写一首关于春天的诗", "model": "gpt-3.5-turbo", "priority": 1}'

# 创建高优先级任务
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "分析市场趋势数据", "model": "gpt-4", "priority": 8}' | jq .
```

#### 获取任务
```bash
# 获取所有任务
curl http://localhost:8000/api/v1/tasks | jq .

# 获取指定任务
curl http://localhost:8000/api/v1/tasks/1 | jq .

# 分页获取任务（跳过前2个，获取5个）
curl "http://localhost:8000/api/v1/tasks?skip=2&limit=5" | jq .
```

#### 错误测试
```bash
# 测试不存在的任务
curl http://localhost:8000/api/v1/tasks/999

# 测试无效数据
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": ""}'  # prompt 为空会报错
```

### 3. Python requests 测试

```python
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_health():
    """测试健康检查"""
    response = requests.get(f"{API_BASE}/health")
    print(f"Health Check: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def create_task(prompt, model="gpt-3.5-turbo", priority=1):
    """创建任务"""
    data = {
        "prompt": prompt,
        "model": model,
        "priority": priority
    }
    response = requests.post(f"{API_BASE}/tasks", json=data)
    print(f"Create Task: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def get_tasks():
    """获取所有任务"""
    response = requests.get(f"{API_BASE}/tasks")
    print(f"Get Tasks: {response.status_code}")
    tasks = response.json()
    print(f"Total tasks: {len(tasks)}")
    print(json.dumps(tasks, indent=2, ensure_ascii=False))
    return tasks

def get_task(task_id):
    """获取指定任务"""
    response = requests.get(f"{API_BASE}/tasks/{task_id}")
    print(f"Get Task {task_id}: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.json()}")
    return response.json() if response.status_code == 200 else None

# 完整测试流程
if __name__ == "__main__":
    print("=== Async AI Task Runner API 测试 ===\n")

    # 1. 健康检查
    print("1. 健康检查")
    test_health()
    print()

    # 2. 创建任务
    print("2. 创建任务")
    task1 = create_task("写一首关于春天的诗", "gpt-3.5-turbo", 1)
    task2 = create_task("分析Python代码性能", "gpt-4", 5)
    print()

    # 3. 获取任务列表
    print("3. 获取任务列表")
    tasks = get_tasks()
    print()

    # 4. 获取单个任务
    if tasks:
        print("4. 获取单个任务")
        get_task(tasks[0]["id"])
        print()

    # 5. 测试错误情况
    print("5. 测试错误情况")
    get_task(999)  # 不存在的任务
```

### 4. Postman 测试

导入以下集合到 Postman：

```json
{
  "info": {
    "name": "Async AI Task Runner API",
    "description": "Async AI Task Runner API 测试集合"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{BASE_URL}}/api/v1/health",
          "host": ["{{BASE_URL}}"],
          "path": ["api", "v1", "health"]
        }
      }
    },
    {
      "name": "Create Task",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"prompt\": \"写一首关于春天的诗\",\n  \"model\": \"gpt-3.5-turbo\",\n  \"priority\": 1\n}"
        },
        "url": {
          "raw": "{{BASE_URL}}/api/v1/tasks",
          "host": ["{{BASE_URL}}"],
          "path": ["api", "v1", "tasks"]
        }
      }
    },
    {
      "name": "Get Tasks",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{BASE_URL}}/api/v1/tasks?skip=0&limit=10",
          "host": ["{{BASE_URL}}"],
          "path": ["api", "v1", "tasks"],
          "query": [
            {
              "key": "skip",
              "value": "0"
            },
            {
              "key": "limit",
              "value": "10"
            }
          ]
        }
      }
    },
    {
      "name": "Get Single Task",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{BASE_URL}}/api/v1/tasks/1",
          "host": ["{{BASE_URL}}"],
          "path": ["api", "v1", "tasks", "1"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "BASE_URL",
      "value": "http://localhost:8000"
    }
  ]
}
```

## 🔧 响应格式

### 成功响应
```json
{
  "prompt": "任务描述",
  "model": "gpt-3.5-turbo",
  "priority": 1,
  "id": 1,
  "status": "PENDING",
  "result": null,
  "created_at": "2025-11-25T03:31:16",
  "updated_at": null
}
```

### 错误响应
```json
{
  "detail": "错误信息描述"
}
```

## 📊 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 💡 测试建议

1. **从简单开始**: 先测试健康检查接口
2. **逐步复杂**: 再测试创建和获取任务
3. **边界情况**: 测试无效参数、不存在的资源等
4. **数据验证**: 检查返回数据的完整性和格式
5. **性能测试**: 创建多个任务测试分页功能

## 🐛 常见问题

### 1. 连接被拒绝
```bash
# 确保应用正在运行
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 数据格式错误
确保 Content-Type 设置正确：
```bash
curl -X POST ... -H "Content-Type: application/json" ...
```

### 3. 中文乱码
Python 请求中设置 ensure_ascii=False：
```python
json.dumps(response.json(), indent=2, ensure_ascii=False)
```

## 📈 下一步

- 添加认证测试（Day 2+）
- 添加异步处理测试（Day 2）
- 添加批量操作测试
- 添加性能和压力测试