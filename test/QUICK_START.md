# 🚀 快速开始指南

## 📋 一分钟快速测试

```bash
# 1. 进入项目目录
cd /Users/lizhao/workspace/python-learn/async-ai-task-runner

# 2. 确保服务运行
docker-compose ps

# 3. 运行完整测试套件
./test/scripts/run-full-integration-test.sh

# 4. 查看测试报告
open test/reports/
```

## 🔧 环境准备检查

```bash
# 检查必需工具
which curl jq bc python3

# 如果缺少工具，安装：
# macOS: brew install jq bc
# Ubuntu: sudo apt-get install jq bc
```

## 📊 单独测试模块

```bash
# 只运行基础连接测试
./test/scripts/basic-connectivity-test.sh

# 运行负载测试
python3 test/scripts/load-test-medium.py --concurrent 20 --requests 5

# 查看测试检查清单
cat test/templates/test-checklist.md
```

## 🎯 测试结果解读

- ✅ **绿色** - 测试通过，系统健康
- ⚠️ **黄色** - 警告，需要关注
- ❌ **红色** - 失败，需要修复

测试报告保存在 `test/reports/` 目录中，包含详细的测试结果和建议。

## 🆘 遇到问题？

1. **PostgreSQL 连接问题**: 检查用户权限配置
2. **服务未启动**: 运行 `docker-compose up -d`
3. **端口冲突**: 确保 8000, 5433, 6379, 5555 端口可用

---

**详细文档**: [完整测试方案](test/integration-test-plan.md) | [测试目录结构](test/README.md)