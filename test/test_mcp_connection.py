#!/usr/bin/env python3
"""
手动测试MCP服务器连接
"""

import subprocess
import json
import sys

def test_mcp_connection():
    """测试MCP服务器连接"""
    print("🔍 测试MCP服务器连接...")

    # 测试工具列表
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }

    try:
        # 运行MCP服务器并发送请求
        process = subprocess.run(
            [sys.executable, "/Users/lizhao/workspace/python-learn/async-ai-task-runner/run_mcp_server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=10
        )

        print(f"📤 发送请求: {json.dumps(request, indent=2)}")
        print(f"📥 响应状态: {process.returncode}")

        if process.returncode == 0:
            print(f"✅ MCP服务器响应:")
            print(process.stdout)
        else:
            print(f"❌ MCP服务器错误:")
            print(process.stderr)

    except subprocess.TimeoutExpired:
        print("❌ 连接超时")
    except Exception as e:
        print(f"❌ 连接失败: {e}")

def test_tool_call():
    """测试工具调用"""
    print("\n🛠️ 测试工具调用...")

    # 测试创建任务工具
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "create_task",
            "arguments": {
                "prompt": "测试MCP连接",
                "model": "deepseek-chat",
                "priority": 5
            }
        }
    }

    try:
        process = subprocess.run(
            [sys.executable, "/Users/lizhao/workspace/python-learn/async-ai-task-runner/run_mcp_server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=15
        )

        print(f"📤 工具调用请求: {json.dumps(request, indent=2)}")
        print(f"📥 响应状态: {process.returncode}")

        if process.returncode == 0:
            print(f"✅ 工具调用响应:")
            print(process.stdout)
        else:
            print(f"❌ 工具调用失败:")
            print(process.stderr)

    except Exception as e:
        print(f"❌ 工具调用测试失败: {e}")

if __name__ == "__main__":
    print("🚀 MCP连接测试")
    print("=" * 50)

    test_mcp_connection()
    test_tool_call()

    print("\n📋 诊断建议:")
    print("1. 如果上述测试成功，MCP服务器工作正常")
    print("2. 如果测试失败，检查:")
    print("   - Python路径和权限")
    print("   - 依赖包是否正确安装")
    print("   - FastAPI服务器是否在8000端口运行")
    print("   - 数据库连接是否正常")
    print("3. 检查Claude Desktop配置文件路径和格式")
    print("4. 重启Claude Desktop并查看日志")