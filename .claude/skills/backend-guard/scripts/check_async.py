#!/usr/bin/env python3
"""
异步代码检查脚本
用于检测 FastAPI 项目中的异步阻塞问题
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

class AsyncBlockerChecker(ast.NodeVisitor):
    """检查异步代码中的阻塞调用"""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []
        self.current_function = None
        self.is_async = False

    def visit_AsyncFunctionDef(self, node):
        """访问异步函数定义"""
        self.is_async = True
        self.current_function = node.name
        self.generic_visit(node)
        self.is_async = False
        self.current_function = None

    def visit_Call(self, node):
        """检查函数调用"""
        if self.is_async:
            # 检查常见的阻塞调用
            if isinstance(node.func, ast.Name):
                func_name = node.func.id

                # time.sleep 阻塞调用
                if func_name == 'sleep':
                    # 检查是否来自 time 模块
                    for parent in ast.walk(ast.parse(ast.unparse(node))):
                        if isinstance(parent, ast.Attribute):
                            if isinstance(parent.value, ast.Name) and parent.value.id == 'time':
                                self.issues.append({
                                    'line': node.lineno,
                                    'function': self.current_function,
                                    'issue': f'在异步函数 {self.current_function} 中使用了 time.sleep',
                                    'suggestion': '使用 asyncio.sleep 替代 time.sleep'
                                })
                                break

            # 检查 requests 库调用
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'requests':
                    self.issues.append({
                        'line': node.lineno,
                        'function': self.current_function,
                        'issue': f'在异步函数 {self.current_function} 中使用了同步 requests 库',
                        'suggestion': '使用 httpx.AsyncClient 替代 requests'
                    })

        self.generic_visit(node)

    def visit_For(self, node):
        """检查循环中的潜在阻塞操作"""
        if self.is_async:
            # 检查是否有同步数据库操作
            if isinstance(node.target, ast.Name) and node.target.id.startswith('result'):
                self.generic_visit(node)
        else:
            self.generic_visit(node)

def check_file(filepath: Path) -> List[Dict[str, Any]]:
    """检查单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        checker = AsyncBlockerChecker(str(filepath))
        checker.visit(tree)
        return checker.issues

    except Exception as e:
        return [{
            'line': 0,
            'function': 'parsing',
            'issue': f'解析文件失败: {e}',
            'suggestion': '检查文件语法是否正确'
        }]

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 检查指定文件或目录
        target_path = Path(sys.argv[1])
    else:
        # 默认检查当前目录下的 app/ 目录
        target_path = Path('app')

    if not target_path.exists():
        print(f"❌ 路径不存在: {target_path}")
        sys.exit(1)

    all_issues = []

    if target_path.is_file():
        python_files = [target_path]
    else:
        python_files = list(target_path.rglob('*.py'))

    for filepath in python_files:
        print(f"🔍 检查文件: {filepath}")
        issues = check_file(filepath)
        if issues:
            all_issues.extend(issues)
            for issue in issues:
                print(f"  ❌ 行 {issue['line']}: {issue['issue']}")
                print(f"     💡 建议: {issue['suggestion']}")
        else:
            print(f"  ✅ 未发现异步阻塞问题")

    print(f"\n📊 总计发现 {len(all_issues)} 个问题")

    if all_issues:
        print("\n🔧 修复建议:")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue['suggestion']}")
        return 1
    else:
        print("🎉 所有代码都符合异步编程规范!")
        return 0

if __name__ == "__main__":
    sys.exit(main())