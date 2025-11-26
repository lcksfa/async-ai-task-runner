#!/usr/bin/env python3
"""
完整的异步任务系统集成测试
验证 FastAPI + Celery + Redis + PostgreSQL 的完整工作流程
"""

import asyncio
import time
import json
import uuid
from datetime import datetime
import requests
import subprocess
import sys
from typing import Dict, Any

# 测试配置
API_BASE_URL = "http://localhost:8000"
FASTAPI_STATUS_URL = f"{API_BASE_URL}/api/v1/health"
TASKS_URL = f"{API_BASE_URL}/api/v1/tasks"
TASK_STATUS_URL = f"{API_BASE_URL}/api/v1/tasks/{{task_id}}"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """打印带状态的消息"""
    if status == "SUCCESS":
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    elif status == "ERROR":
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    elif status == "WARNING":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    elif status == "INFO":
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    else:
        print(f"{message}")

def test_service_health():
    """测试所有服务健康状态"""
    print_status("="*50)
    print_status("🏥 开始服务健康检查", "INFO")
    print_status("="*50)

    results = {}

    # 1. 测试 FastAPI 服务
    try:
        response = requests.get(FASTAPI_STATUS_URL, timeout=5)
        if response.status_code in [200, 201]:
            health_data = response.json()
            print_status(f"FastAPI 服务: {health_data.get('status', 'Unknown')}", "SUCCESS")
            results["fastapi"] = True
        else:
            print_status(f"FastAPI 服务状态码: {response.status_code}", "ERROR")
            results["fastapi"] = False
    except Exception as e:
        print_status(f"FastAPI 服务连接失败: {e}", "ERROR")
        results["fastapi"] = False

    # 2. 测试 Celery Worker
    try:
        from app.worker.app import celery_app
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats:
            worker_count = len(stats)
            print_status(f"Celery Workers: {worker_count} 个在线", "SUCCESS")
            for worker_name, worker_stats in stats.items():
                print_status(f"  - {worker_name}: {worker_stats.get('pool', {}).get('max-concurrency', 'Unknown')} 并发", "INFO")
            results["celery"] = True
        else:
            print_status("Celery Workers: 未找到在线 Worker", "WARNING")
            results["celery"] = False
    except Exception as e:
        print_status(f"Celery 连接失败: {e}", "ERROR")
        results["celery"] = False

    # 3. 测试 Redis 连接
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.redis_url)
        r.ping()
        print_status("Redis 连接: 正常", "SUCCESS")
        results["redis"] = True
    except Exception as e:
        print_status(f"Redis 连接失败: {e}", "ERROR")
        results["redis"] = False

    # 4. 测试数据库连接
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async def test_db():
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("SELECT 1"))
                return result.scalar()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        db_result = loop.run_until_complete(test_db())
        loop.close()

        if db_result == 1:
            print_status("PostgreSQL 连接: 正常", "SUCCESS")
            results["database"] = True
        else:
            print_status("PostgreSQL 查询异常", "ERROR")
            results["database"] = False
    except Exception as e:
        print_status(f"PostgreSQL 连接失败: {e}", "ERROR")
        results["database"] = False

    return results

def test_celery_tasks_directly():
    """直接测试 Celery 任务"""
    print_status("\n" + "="*50)
    print_status("🔧 直接测试 Celery 任务", "INFO")
    print_status("="*50)

    try:
        from app.worker.tasks.demo_tasks import simple_calculation, send_notification_email
        from app.worker.tasks.ai_tasks import run_ai_text_generation

        # 测试 1: 简单计算任务
        print_status("测试 1: 简单计算任务", "INFO")
        calc_result = simple_calculation.delay(15, 25, "multiply")
        print_status(f"  任务ID: {calc_result.id}", "INFO")

        # 等待任务完成
        for i in range(10):
            if calc_result.ready():
                result = calc_result.get()
                expected = 15 * 25
                if result.get('result') == expected:
                    print_status(f"  计算结果: 15 * 25 = {expected} ✅", "SUCCESS")
                else:
                    print_status(f"  计算结果错误: 期望 {expected}, 实际 {result.get('result')}", "ERROR")
                break
            time.sleep(0.5)
        else:
            print_status("  计算任务超时", "ERROR")

        # 测试 2: 邮件发送任务
        print_status("\n测试 2: 邮件发送任务", "INFO")
        email_result = send_notification_email.delay(
            recipient="test@example.com",
            subject="集成测试邮件",
            message="这是一封测试邮件"
        )
        print_status(f"  任务ID: {email_result.id}", "INFO")

        for i in range(15):
            if email_result.ready():
                email_data = email_result.get()
                if email_data.get('status') == 'success':
                    print_status(f"  邮件发送成功: {email_data.get('recipient')}", "SUCCESS")
                else:
                    print_status(f"  邮件发送失败", "ERROR")
                break
            time.sleep(1)
        else:
            print_status("  邮件任务超时", "ERROR")

        return True

    except Exception as e:
        print_status(f"Celery 任务测试失败: {e}", "ERROR")
        return False

def test_fastapi_task_submission():
    """测试 FastAPI 任务提交和状态查询"""
    print_status("\n" + "="*50)
    print_status("🌐 测试 FastAPI 任务集成", "INFO")
    print_status("="*50)

    try:
        # 测试 1: 提交 AI 文本生成任务
        test_prompt = "请解释什么是异步编程"
        task_data = {
            "prompt": test_prompt,
            "model": "gpt-3.5-turbo",
            "priority": 5
        }

        print_status(f"提交任务: {test_prompt}", "INFO")
        response = requests.post(TASKS_URL, json=task_data, timeout=10)

        if response.status_code in [200, 201]:
            task_info = response.json()
            task_id = task_info.get('id')
            print_status(f"任务提交成功, ID: {task_id}", "SUCCESS")
            print_status(f"初始状态: {task_info.get('status')}", "INFO")

            # 测试 2: 轮询任务状态
            print_status("\n轮询任务状态...", "INFO")
            max_wait_time = 60  # 最多等待60秒
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                status_response = requests.get(TASK_STATUS_URL.format(task_id=task_id), timeout=5)

                if status_response.status_code == 200:
                    task_status = status_response.json()
                    current_status = task_status.get('status')
                    result = task_status.get('result')

                    print_status(f"  状态更新: {current_status}", "INFO")

                    if current_status in ['COMPLETED', 'FAILED']:
                        if current_status == 'COMPLETED' and result:
                            print_status(f"任务完成! 结果长度: {len(result)} 字符", "SUCCESS")
                            print_status(f"结果预览: {result[:100]}...", "INFO")
                            return True
                        else:
                            print_status(f"任务失败或无结果", "ERROR")
                            return False

                    time.sleep(2)  # 每2秒检查一次
                else:
                    print_status(f"状态查询失败: {status_response.status_code}", "ERROR")
                    return False

            print_status("任务执行超时", "ERROR")
            return False
        else:
            print_status(f"任务提交失败: {response.status_code} - {response.text}", "ERROR")
            return False

    except Exception as e:
        print_status(f"FastAPI 集成测试失败: {e}", "ERROR")
        return False

def test_concurrent_tasks():
    """测试并发任务处理"""
    print_status("\n" + "="*50)
    print_status("🚀 测试并发任务处理", "INFO")
    print_status("="*50)

    try:
        # 同时提交多个任务
        tasks = []
        task_prompts = [
            "什么是机器学习？",
            "解释Python的GIL",
            "什么是RESTful API？",
            "数据库索引的作用",
            "容器化技术的优势"
        ]

        print_status(f"同时提交 {len(task_prompts)} 个AI任务...", "INFO")

        # 提交任务
        for i, prompt in enumerate(task_prompts):
            task_data = {
                "prompt": prompt,
                "model": "gpt-3.5-turbo",
                "priority": i + 1
            }

            response = requests.post(TASKS_URL, json=task_data, timeout=10)
            if response.status_code in [200, 201]:
                task_info = response.json()
                tasks.append({
                    'id': task_info.get('id'),
                    'prompt': prompt,
                    'submitted_at': time.time()
                })
                print_status(f"  任务 {i+1} 提交成功: {task_info.get('id')}", "SUCCESS")
            else:
                print_status(f"  任务 {i+1} 提交失败", "ERROR")

        print_status(f"\n监控 {len(tasks)} 个任务执行情况...", "INFO")

        # 监控任务执行
        completed_tasks = 0
        start_time = time.time()
        max_wait_time = 120  # 最多等待2分钟

        while completed_tasks < len(tasks) and time.time() - start_time < max_wait_time:
            for task in tasks:
                if 'completed_at' not in task:
                    try:
                        response = requests.get(TASK_STATUS_URL.format(task_id=task['id']), timeout=5)
                        if response.status_code in [200, 201]:
                            task_status = response.json()
                            current_status = task_status.get('status')

                            if current_status in ['COMPLETED', 'FAILED']:
                                task['completed_at'] = time.time()
                                task['status'] = current_status
                                completed_tasks += 1

                                duration = task['completed_at'] - task['submitted_at']
                                if current_status == 'COMPLETED':
                                    print_status(f"  任务完成: {task['prompt'][:30]}... (耗时: {duration:.1f}s)", "SUCCESS")
                                else:
                                    print_status(f"  任务失败: {task['prompt'][:30]}...", "ERROR")
                    except:
                        pass

            if completed_tasks < len(tasks):
                time.sleep(3)  # 每3秒检查一次

        # 统计结果
        successful_tasks = sum(1 for task in tasks if task.get('status') == 'COMPLETED')
        total_time = time.time() - start_time

        print_status(f"\n并发测试结果:", "INFO")
        print_status(f"  总任务数: {len(tasks)}", "INFO")
        print_status(f"  成功任务: {successful_tasks}", "SUCCESS" if successful_tasks == len(tasks) else "WARNING")
        print_status(f"  失败任务: {len(tasks) - successful_tasks}", "INFO")
        print_status(f"  总耗时: {total_time:.1f}s", "INFO")
        print_status(f"  平均耗时: {total_time/len(tasks):.1f}s", "INFO")

        return successful_tasks == len(tasks)

    except Exception as e:
        print_status(f"并发测试失败: {e}", "ERROR")
        return False

def test_error_handling():
    """测试错误处理"""
    print_status("\n" + "="*50)
    print_status("🛡️ 测试错误处理", "INFO")
    print_status("="*50)

    try:
        # 测试 1: 无效的任务数据
        print_status("测试 1: 无效任务数据", "INFO")
        invalid_data = {
            "prompt": "",  # 空提示
            "model": "invalid-model"
        }

        response = requests.post(TASKS_URL, json=invalid_data, timeout=5)
        if response.status_code >= 400:
            print_status("  无效数据正确被拒绝", "SUCCESS")
        else:
            print_status("  无效数据未被正确处理", "ERROR")

        # 测试 2: 查询不存在的任务
        print_status("\n测试 2: 查询不存在的任务", "INFO")
        fake_task_id = str(uuid.uuid4())
        response = requests.get(TASK_STATUS_URL.format(task_id=fake_task_id), timeout=5)

        if response.status_code in [404, 422]:
            print_status(f"  不存在任务正确处理: 状态码 {response.status_code}", "SUCCESS")
        else:
            print_status(f"  不存在任务返回状态码: {response.status_code}", "ERROR")

        return True

    except Exception as e:
        print_status(f"错误处理测试失败: {e}", "ERROR")
        return False

def generate_test_report(health_results, task_results):
    """生成测试报告"""
    print_status("\n" + "="*60)
    print_status("📊 集成测试报告", "INFO")
    print_status("="*60)

    # 服务健康状态
    print_status("\n🏥 服务健康状态:", "INFO")
    for service, status in health_results.items():
        status_text = "✅ 正常" if status else "❌ 异常"
        color = "SUCCESS" if status else "ERROR"
        print_status(f"  {service.capitalize()}: {status_text}", color)

    # 功能测试结果
    print_status("\n🧪 功能测试结果:", "INFO")
    total_tests = len(task_results)
    passed_tests = sum(1 for result in task_results.values() if result)

    for test_name, result in task_results.items():
        status_text = "✅ 通过" if result else "❌ 失败"
        color = "SUCCESS" if result else "ERROR"
        print_status(f"  {test_name}: {status_text}", color)

    # 总体评估
    print_status(f"\n📈 总体评估:", "INFO")
    print_status(f"  通过测试: {passed_tests}/{total_tests}", "SUCCESS" if passed_tests == total_tests else "WARNING")

    all_services_healthy = all(health_results.values())
    all_tests_passed = passed_tests == total_tests

    if all_services_healthy and all_tests_passed:
        print_status(f"  系统状态: 🟢 完全正常", "SUCCESS")
        return True
    elif all_services_healthy:
        print_status(f"  系统状态: 🟡 部分功能异常", "WARNING")
        return False
    else:
        print_status(f"  系统状态: 🔴 服务异常", "ERROR")
        return False

def main():
    """主测试函数"""
    print_status("🚀 Async AI Task Runner 完整集成测试", "INFO")
    print_status(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")

    # 1. 服务健康检查
    health_results = test_service_health()

    # 如果服务不健康，提前结束
    if not all(health_results.values()):
        print_status("\n❌ 部分服务不健康，跳过功能测试", "ERROR")
        task_results = {}
        return generate_test_report(health_results, task_results)

    # 2. 功能测试
    task_results = {}

    task_results["Celery任务直接调用"] = test_celery_tasks_directly()
    task_results["FastAPI任务集成"] = test_fastapi_task_submission()
    task_results["并发任务处理"] = test_concurrent_tasks()
    task_results["错误处理机制"] = test_error_handling()

    # 3. 生成报告
    return generate_test_report(health_results, task_results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("\n⚠️  测试被用户中断", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"\n💥 测试发生未预期错误: {e}", "ERROR")
        sys.exit(1)