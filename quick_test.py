#!/usr/bin/env python3
"""
快速测试核心功能
"""

import requests
import time
import json

# 测试配置
API_BASE_URL = "http://localhost:8000"

def test_basic_workflow():
    """测试基本工作流程"""
    print("🚀 测试 FastAPI + Celery 基本工作流程")

    # 1. 测试健康检查
    print("\n1. 测试健康检查...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ FastAPI 服务正常: {response.json()}")
        else:
            print(f"❌ FastAPI 服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FastAPI 连接失败: {e}")
        return False

    # 2. 提交 AI 任务
    print("\n2. 提交 AI 任务...")
    task_data = {
        "prompt": "什么是人工智能？",
        "model": "gpt-3.5-turbo",
        "priority": 5
    }

    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/tasks", json=task_data, timeout=10)
        if response.status_code in [200, 201]:
            task_info = response.json()
            task_id = task_info.get('id')
            print(f"✅ 任务提交成功: ID={task_id}, 状态={task_info.get('status')}")
        else:
            print(f"❌ 任务提交失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 任务提交异常: {e}")
        return False

    # 3. 监控任务状态
    print("\n3. 监控任务状态...")
    max_wait = 30
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/tasks/{task_id}", timeout=5)
            if response.status_code == 200:
                task_status = response.json()
                status = task_status.get('status')
                print(f"   状态更新: {status}")

                if status == 'COMPLETED':
                    result = task_status.get('result', '')
                    print(f"✅ 任务完成! 结果长度: {len(result)} 字符")
                    print(f"📄 结果预览: {result[:100]}...")
                    return True
                elif status == 'FAILED':
                    print(f"❌ 任务失败: {task_status.get('result', '')}")
                    return False

            time.sleep(3)
        except Exception as e:
            print(f"❌ 状态查询失败: {e}")
            return False

    print("⚠️ 任务执行超时")
    return False

def test_celery_direct():
    """直接测试 Celery 任务"""
    print("\n🔧 直接测试 Celery 任务")

    try:
        from app.worker.tasks.demo_tasks import simple_calculation

        # 测试计算任务
        print("测试简单计算任务...")
        result = simple_calculation.delay(10, 20, "add")
        print(f"任务ID: {result.id}")

        # 等待完成
        for i in range(10):
            if result.ready():
                task_result = result.get()
                if task_result.get('result') == 30:
                    print("✅ 计算任务成功: 10 + 20 = 30")
                    return True
                else:
                    print(f"❌ 计算结果错误: {task_result}")
                    return False
            print(f"   等待中... ({i+1}/10)")
            time.sleep(1)

        print("❌ 计算任务超时")
        return False

    except Exception as e:
        print(f"❌ Celery 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("🧪 Async AI Task Runner 快速测试")
    print("="*50)

    success1 = test_celery_direct()
    success2 = test_basic_workflow()

    print("\n" + "="*50)
    print("📊 测试结果:")
    print(f"  Celery 任务: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"  API 集成: {'✅ 通过' if success2 else '❌ 失败'}")

    if success1 and success2:
        print("🎉 所有测试通过! 系统运行正常")
    else:
        print("⚠️ 部分测试失败，请检查系统状态")