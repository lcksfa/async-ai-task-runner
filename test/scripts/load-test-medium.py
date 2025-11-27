#!/usr/bin/env python3
"""
Async AI Task Runner 中等负载测试工具

用途: 测试系统在中等并发负载下的性能表现
用法: python load-test-medium.py [--concurrent 50] [--requests 10] [--url http://localhost:8000]
"""

import asyncio
import aiohttp
import time
import json
import argparse
import statistics
from datetime import datetime
from typing import List, Dict, Any, Tuple

class LoadTestResult:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.created_tasks = []

    def add_success(self, response_time: float, task_data: Dict[str, Any]):
        self.successful_requests += 1
        self.response_times.append(response_time)
        self.created_tasks.append(task_data)

    def add_failure(self, error: str):
        self.failed_requests += 1
        self.errors.append(error)

    def get_summary(self) -> Dict[str, Any]:
        if not self.response_times:
            return {
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'median_response_time': 0
            }

        return {
            'avg_response_time': statistics.mean(self.response_times),
            'min_response_time': min(self.response_times),
            'max_response_time': max(self.response_times),
            'median_response_time': statistics.median(self.response_times)
        }

async def create_task(session: aiohttp.ClientSession, url: str, task_id: int) -> Tuple[float, Dict[str, Any], str]:
    """创建单个任务并返回结果"""
    task_data = {
        "prompt": f"负载测试任务 {task_id}：请计算 {task_id} × 2",
        "model": "deepseek-chat",
        "priority": task_id % 5 + 1
    }

    start_time = time.time()
    error_message = ""

    try:
        async with session.post(
            f"{url}/api/v1/tasks",
            json=task_data,
            headers={"accept": "application/json"}
        ) as response:
            response_text = await response.text()
            response_time = time.time() - start_time

            if response.status == 200:
                try:
                    response_data = json.loads(response_text)
                    return response_time, response_data, ""
                except json.JSONDecodeError:
                    error_message = f"Invalid JSON: {response_text[:100]}"
                    return response_time, {}, error_message
            else:
                error_message = f"HTTP {response.status}: {response_text[:100]}"
                return response_time, {}, error_message

    except Exception as e:
        response_time = time.time() - start_time
        error_message = f"Request failed: {str(e)}"
        return response_time, {}, error_message

async def run_load_test(concurrent: int, requests_per_batch: int, base_url: str) -> LoadTestResult:
    """运行负载测试"""
    result = LoadTestResult()
    result.start_time = datetime.now()

    print(f"🚀 开始中等负载测试")
    print(f"并发数: {concurrent}")
    print(f"每批请求数: {requests_per_batch}")
    print(f"总请求数: {concurrent * requests_per_batch}")
    print("-" * 50)

    connector = aiohttp.TCPConnector(limit=concurrent * 2, limit_per_host=concurrent)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # 执行并发测试
        for batch in range(requests_per_batch):
            print(f"执行第 {batch + 1}/{requests_per_batch} 批请求...")

            # 创建并发任务
            tasks = []
            for i in range(concurrent):
                task_id = batch * concurrent + i + 1
                task = create_task(session, base_url, task_id)
                tasks.append(task)

            # 等待所有请求完成
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for response_time, task_data, error in batch_results:
                result.total_requests += 1

                if isinstance(task_data, dict) and task_data.get('id') and not error:
                    result.add_success(response_time, task_data)
                else:
                    result.add_failure(error if error else "Unknown error")

            # 显示批次统计
            batch_success = sum(1 for r in batch_results if isinstance(r, tuple) and r[1].get('id'))
            avg_time = statistics.mean([r[0] for r in batch_results if isinstance(r, tuple)]) if batch_results else 0

            print(f"批次 {batch + 1}: 成功 {batch_success}/{concurrent}, 平均响应时间: {avg_time:.3f}s")

            # 短暂休息，避免过载
            if batch < requests_per_batch - 1:
                await asyncio.sleep(1)

    result.end_time = datetime.now()
    return result

def print_results(result: LoadTestResult):
    """打印测试结果"""
    print("-" * 50)
    print("📊 负载测试结果")
    print("-" * 50)

    duration = (result.end_time - result.start_time).total_seconds()

    print(f"测试时间: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {result.end_time.strftime('%Y-%m:%d:%S')}")
    print(f"总耗时: {duration:.2f} 秒")
    print(f"总请求数: {result.total_requests}")
    print(f"成功请求: {result.successful_requests}")
    print(f"失败请求: {result.failed_requests}")
    print(f"成功率: {(result.successful_requests / result.total_requests * 100):.1f}%")

    if result.response_times:
        stats = result.get_summary()
        print(f"\n📈 响应时间统计:")
        print(f"  平均响应时间: {stats['avg_response_time']:.3f}s")
        print(f"  最小响应时间: {stats['min_response_time']:.3f}s")
        print(f"  最大响应时间: {stats['max_response_time']:.3f}s")
        print(f"  中位数响应时间: {stats['median_response_time']:.3f}s")

        # 响应时间分布
        response_buckets = {
            '< 100ms': sum(1 for t in result.response_times if t < 0.1),
            '100-200ms': sum(1 for t in result.response_times if 0.1 <= t < 0.2),
            '200-500ms': sum(1 for t in result.response_times if 0.2 <= t < 0.5),
            '500ms-1s': sum(1 for t in result.response_times if 0.5 <= t < 1.0),
            '>= 1s': sum(1 for t in result.response_times if t >= 1.0)
        }

        print(f"\n📊 响应时间分布:")
        for bucket, count in response_buckets.items():
            percentage = count / len(result.response_times) * 100
            print(f"  {bucket}: {count} ({percentage:.1f}%)")

    # 性能指标
    rps = result.total_requests / duration if duration > 0 else 0
    success_rps = result.successful_requests / duration if duration > 0 else 0

    print(f"\n⚡ 性能指标:")
    print(f"  总吞吐量: {rps:.2f} RPS (每秒请求数)")
    print(f"  成功吞吐量: {success_rps:.2f} RPS")
    print(f"  平均 QPS: {result.successful_requests / (result.end_time - result.start_time).total_seconds():.2f}")

    # 错误统计
    if result.errors:
        print(f"\n❌ 错误统计:")
        error_counts = {}
        for error in result.errors:
            error_type = error.split(':')[0] if ':' in error else 'Other'
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

        for error_type, count in error_counts.items():
            print(f"  {error_type}: {count}")

    # 成功任务ID范围
    if result.created_tasks:
        task_ids = [task['id'] for task in result.created_tasks if task.get('id')]
        print(f"\n✅ 成功创建的任务ID范围: {min(task_ids)} - {max(task_ids)}")

def save_results(result: LoadTestResult, filename: str = None):
    """保存测试结果到文件"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"load_test_result_{timestamp}.json"

    stats = result.get_summary()

    report_data = {
        "test_info": {
            "timestamp": result.start_time.isoformat(),
            "duration_seconds": (result.end_time - result.start_time).total_seconds(),
            "total_requests": result.total_requests,
            "successful_requests": result.successful_requests,
            "failed_requests": result.failed_requests,
            "success_rate": result.successful_requests / result.total_requests * 100
        },
        "performance_stats": {
            "avg_response_time": stats['avg_response_time'],
            "min_response_time": stats['min_response_time'],
            "max_response_time': stats['max_response_time'],
            "median_response_time": stats['median_response_time']
        },
        "created_tasks": result.created_tasks,
        "errors": result.errors
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"\n📄 详细测试结果已保存到: {filename}")

async def main():
    parser = argparse.ArgumentParser(description='Async AI Task Runner 负载测试工具')
    parser.add_argument('--concurrent', type=int, default=50, help='并发请求数 (默认: 50)')
    parser.add_argument('--requests', type=int, default=10, help='每批请求数 (默认: 10)')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='API 基础 URL (默认: http://localhost:8000)')
    parser.add_argument('--save', action='store_true', help='保存测试结果到文件')

    args = parser.parse_args()

    print("🔬 Async AI Task Runner 中等负载测试")
    print("=" * 50)

    try:
        # 运行负载测试
        result = await run_load_test(args.concurrent, args.requests, args.url)

        # 打印结果
        print_results(result)

        # 保存结果
        if args.save:
            save_results(result)

        # 设置退出码
        if result.failed_requests == 0:
            print("\n🎉 所有请求都成功完成！")
            exit(0)
        elif result.successful_requests / result.total_requests > 0.95:
            print(f"\n⚠️ 大部分请求成功 ({result.successful_requests}/{result.total_requests})")
            exit(0)
        else:
            print(f"\n❌ 失败请求过多 ({result.failed_requests}/{result.total_requests})")
            exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n💥 测试执行失败: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())