#!/usr/bin/env python3
"""
Async AI Task Runner API 测试脚本

运行此脚本前请确保：
1. 应用已启动：uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
2. 安装了 requests 库：uv add requests
"""

import requests
import json
import time
from typing import Dict, List, Any

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.created_tasks = []

    def print_separator(self, title: str):
        """打印分隔符"""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)

    def print_response(self, response: requests.Response, title: str = ""):
        """格式化打印响应"""
        if title:
            print(f"\n📋 {title}")

        print(f"🌐 状态码: {response.status_code}")

        try:
            data = response.json()
            print(f"📄 响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        except:
            print(f"📄 响应文本: {response.text}")
            return response.text

    def test_health(self):
        """测试健康检查"""
        self.print_separator("健康检查测试")

        try:
            response = requests.get(f"{self.api_base}/health")
            self.print_response(response, "健康检查接口")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败！请确保应用正在运行")
            print(f"📝 启动命令: uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return False

    def test_create_task(self, prompt: str, model: str = "gpt-3.5-turbo", priority: int = 1):
        """创建任务"""
        data = {
            "prompt": prompt,
            "model": model,
            "priority": priority
        }

        try:
            response = requests.post(
                f"{self.api_base}/tasks",
                json=data,
                headers={"Content-Type": "application/json"}
            )

            result = self.print_response(response, f"创建任务: {prompt[:30]}...")

            if response.status_code == 201:
                self.created_tasks.append(result["id"])
                return result
            else:
                print("❌ 创建任务失败")
                return None

        except Exception as e:
            print(f"❌ 创建任务异常: {e}")
            return None

    def test_get_tasks(self, skip: int = 0, limit: int = 10):
        """获取任务列表"""
        url = f"{self.api_base}/tasks?skip={skip}&limit={limit}"

        try:
            response = requests.get(url)
            result = self.print_response(response, f"获取任务列表 (skip={skip}, limit={limit})")
            return result if response.status_code == 200 else None
        except Exception as e:
            print(f"❌ 获取任务列表异常: {e}")
            return None

    def test_get_task(self, task_id: int):
        """获取单个任务"""
        try:
            response = requests.get(f"{self.api_base}/tasks/{task_id}")
            result = self.print_response(response, f"获取任务 #{task_id}")
            return result if response.status_code == 200 else None
        except Exception as e:
            print(f"❌ 获取任务异常: {e}")
            return None

    def test_error_cases(self):
        """测试错误情况"""
        self.print_separator("错误情况测试")

        # 测试不存在的任务
        print("\n🔍 测试不存在的任务")
        response = requests.get(f"{self.api_base}/tasks/99999")
        self.print_response(response, "获取不存在的任务")

        # 测试无效的任务创建
        print("\n🔍 测试无效的任务创建")
        invalid_data = {
            "prompt": "",  # 空提示语
            "model": "gpt-3.5-turbo",
            "priority": 15  # 超出范围的优先级
        }

        response = requests.post(
            f"{self.api_base}/tasks",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        self.print_response(response, "创建无效任务")

    def test_pagination(self):
        """测试分页功能"""
        self.print_separator("分页功能测试")

        # 创建多个任务用于测试分页
        print("📝 创建测试任务...")
        for i in range(5):
            self.test_create_task(f"测试任务 {i+1}", "gpt-3.5-turbo", i+1)
            time.sleep(0.1)  # 避免创建时间相同

        # 测试分页
        print("\n📄 测试第一页（限制2个）")
        tasks_page1 = self.test_get_tasks(skip=0, limit=2)

        print("\n📄 测试第二页（跳过2个，限制2个）")
        tasks_page2 = self.test_get_tasks(skip=2, limit=2)

        print("\n📄 获取所有任务")
        all_tasks = self.test_get_tasks(skip=0, limit=100)

        if all_tasks:
            print(f"\n📊 总任务数: {len(all_tasks)}")
            print(f"📊 当前页任务数: {len(tasks_page1) if tasks_page1 else 0}")

    def run_full_test(self):
        """运行完整测试流程"""
        print("🚀 Async AI Task Runner API 完整测试开始")
        print(f"🌐 目标地址: {self.base_url}")

        # 1. 健康检查
        if not self.test_health():
            return False

        # 2. 基础功能测试
        self.print_separator("基础功能测试")

        # 创建不同类型的任务
        task1 = self.test_create_task("写一首关于春天的诗", "gpt-3.5-turbo", 1)
        task2 = self.test_create_task("分析市场趋势数据", "gpt-4", 5)
        task3 = self.test_create_task("优化数据库查询", "claude-3-sonnet", 8)

        # 获取任务列表
        tasks = self.test_get_tasks()

        # 获取单个任务
        if tasks:
            self.test_get_task(tasks[0]["id"])

        # 3. 分页测试
        self.test_pagination()

        # 4. 错误测试
        self.test_error_cases()

        # 5. 总结
        self.print_separator("测试总结")
        print(f"✅ 成功创建任务数: {len(self.created_tasks)}")
        print("🎉 API 测试完成！")

        return True

def main():
    """主函数"""
    import sys

    # 检查是否需要显示帮助
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("""
Async AI Task Runner API 测试工具

用法:
    python test_api.py [选项]

选项:
    -h, --help     显示此帮助信息
    --health       仅运行健康检查
    --create       仅运行创建任务测试
    --get          仅运行获取任务测试
    --errors       仅运行错误情况测试
    --pagination   仅运行分页测试

运行前请确保:
1. 应用已启动: uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
2. 安装依赖: uv add requests
        """)
        return

    tester = APITester()

    # 根据参数运行特定测试
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "--health":
            tester.test_health()
        elif test_type == "--create":
            tester.test_create_task("测试创建任务")
        elif test_type == "--get":
            tester.test_get_tasks()
        elif test_type == "--errors":
            tester.test_error_cases()
        elif test_type == "--pagination":
            tester.test_pagination()
        else:
            print(f"未知参数: {test_type}")
            print("使用 --help 查看帮助信息")
    else:
        # 运行完整测试
        tester.run_full_test()

if __name__ == "__main__":
    main()