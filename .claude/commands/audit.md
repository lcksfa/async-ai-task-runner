---
description: 执行 QA 代码审计
---

# 🔍 代码质量审计

## 角色激活
立即作为 **QA Bot** (定义在 `agents/qa.md` 中) 开始工作。

## 📋 审计任务

### 主要目标
对 Async AI Task Runner 项目进行严格的代码质量审计，确保代码符合生产环境标准。

### 审计范围
1. **核心应用文件**:
   - `app/main.py` - FastAPI 应用主文件
   - `app/models.py` - SQLAlchemy 数据库模型
   - `app/schemas.py` - Pydantic 数据验证模式
   - `app/database.py` - 数据库连接和会话管理
   - `app/crud.py` - 数据库操作逻辑 (如果存在)

2. **配置文件**:
   - `requirements.txt` 或 `pyproject.toml` - 项目依赖
   - `.env` - 环境变量配置
   - `alembic.ini` - Alembic 迁移配置
   - `alembic/env.py` - 迁移环境配置

### 重点关注领域

#### 🚨 严重问题检查 (CRITICAL)
- **异步阻塞**: 在 `async def` 中使用同步 I/O (`time.sleep`, `requests`)
- **依赖注入**: 数据库 `Session` 未通过 `Depends()` 正确注入
- **模型混用**: API 返回原始 SQLAlchemy 模型而非 Pydantic 模式
- **会话泄漏**: 异步数据库会话管理不当

#### ⚠️ 警告问题检查 (WARNING)
- **异常处理**: 缺少适当的 `HTTPException` 处理
- **数据验证**: Pydantic 模式定义不完整或不正确
- **路由设计**: RESTful API 设计不规范
- **类型安全**: 缺少类型注解或类型使用不当

#### 💡 优化建议 (SUGGESTION)
- **代码结构**: 模块组织和可维护性改进
- **性能优化**: 潜在的性能瓶颈和优化机会
- **文档完善**: 注释、文档字符串的添加建议
- **最佳实践**: FastAPI 和现代 Python 开发最佳实践

### Async AI Task Runner 专项检查

#### 1. 异步安全性验证
```python
# ❌ 需要检查的常见错误
async def create_task(task_data):
    time.sleep(1)  # 同步阻塞
    result = requests.get("https://api.example.com")  # 同步 HTTP 调用

# ✅ 期望的正确模式
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session)
):
    await asyncio.sleep(1)  # 异步等待
    async with httpx.AsyncClient() as client:  # 异步 HTTP 客户端
        result = await client.get("https://api.example.com")
```

#### 2. 依赖注入模式检查
```python
# ❌ 错误：手动创建会话
async def get_tasks():
    with async_session() as session:
        result = await session.execute(...)

# ✅ 正确：使用依赖注入
async def get_tasks(session: AsyncSession = Depends(get_session)):
    result = await session.execute(...)
```

#### 3. 模型分离原则检查
```python
# ❌ 错误：直接暴露数据库模型
@app.post("/tasks", response_model=Task)
async def create_task(...):

# ✅ 正确：使用响应模式
@app.post("/tasks", response_model=TaskResponse)
async def create_task(...):
```

#### 4. 环境配置安全检查
- API 密钥和敏感信息是否正确使用环境变量
- 数据库连接字符串是否安全配置
- 开发和生产环境配置是否正确分离

## 🔧 执行步骤

### 第一步：代码扫描
- 遍历项目目录结构
- 识别所有相关的 Python 文件
- 检查配置文件的完整性

### 第二步：静态分析
- 应用 `backend-guard` 技能中的审计清单
- 使用提供的异步检查脚本 (如果需要)
- 分析代码模式和潜在问题

### 第三步：生成报告
- 按照严重程度分类问题
- 提供具体的修复建议和代码示例
- 评估代码质量得分和生产就绪性

### 第四步：提供改进路径
- 明确指出必须修复的问题
- 给出可选的优化建议
- 建议后续的改进优先级

## 📊 预期输出格式

```markdown
# 📋 QA 代码审计报告

## 🔍 审计概览
- **审计时间**: [当前时间戳]
- **审计范围**: [扫描的文件列表]
- **发现问题**: [问题总数] 个 (CRITICAL: [x], WARNING: [y], SUGGESTION: [z])

---

## 🚨 严重问题 (CRITICAL) - 必须修复

### 1. 异步阻塞问题
- **文件**: `app/main.py:42`
- **问题**: 在异步函数 `create_task` 中使用了同步的 `time.sleep()`
- **影响**: 会阻塞整个事件循环，严重影响应用性能
- **修复**: 替换为 `await asyncio.sleep(1)`
- **代码示例**:
  ```python
  # 当前代码
  async def create_task(...):
      time.sleep(1)  # ❌ 阻塞操作

  # 修复后代码
  async def create_task(...):
      await asyncio.sleep(1)  # ✅ 异步操作
  ```

---

## ⚠️ 警告问题 (WARNING) - 建议修复

### 1. 缺少异常处理
- **文件**: `app/crud.py:15`
- **问题**: 数据库操作缺少异常处理机制
- **影响**: 数据库错误时可能导致应用崩溃
- **修复**: 添加 try-catch 块处理数据库异常

---

## 💡 优化建议 (SUGGESTION) - 可选改进

### 1. 代码结构优化
- **建议**: 将 CRUD 操作从 `main.py` 中分离到独立的服务层
- **理由**: 提高代码的可维护性和可测试性

---

## ✅ 修复检查清单
- [ ] 修复所有严重问题 (CRITICAL)
- [ ] 解决警告问题 (WARNING)
- [ ] 考虑实施优化建议 (SUGGESTION)
- [ ] 重新运行 QA 审计验证修复

---

## 📊 代码质量评分
- **当前得分**: [0-100] 分
- **生产就绪**: [是/否]
- **建议操作**: [立即修复/可以部署/需要重构]

---

## 🎯 下一步行动
1. **立即修复**: 首先解决所有严重问题
2. **测试验证**: 运行应用确保修复有效
3. **持续改进**: 考虑实施优化建议
4. **定期审计**: 建立定期的代码质量检查流程
```

## ⚡ 快速命令

如果需要额外的代码分析工具，可以使用：
```bash
# 运行异步阻塞检查脚本
python .claude/skills/backend-guard/scripts/check_async.py app/

# 检查项目依赖安全
pip-audit

# 运行代码格式检查
flake8 app/ --max-line-length=100
black app/ --check
```

## 🎯 成功标准
审计成功的标准：
- 发现所有潜在的代码质量问题
- 提供具体可执行的修复建议
- 给出明确的优先级指导
- 帮助提升代码到生产就绪水平

记住：**严格把关，质量第一！你的目标是确保每一行代码都符合生产环境的标准。**