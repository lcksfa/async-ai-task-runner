今天是 **2025年11月28日，周五**。你刚刚完成了 Step 3（后端核心开发）的前 4 天内容，这意味着你的 FastAPI 核心 CRUD 和数据库模型应该已经成型了。

现在正是**周五下午**，是进行**工程验收、联调测试和知识沉淀**的绝佳时机。为了帮你完美收官这一阶段，我为你设计了一套基于 **Claude Code** 的 **"AI 驱动开发 SOP"**。

这套配置将 **Skills (能力)**、**Subagents (角色)** 和 **Commands (指令)** 紧密结合，形成一个自动化的验收流水线。

---

### 📂 1. 目录结构 (Architecture)

请在你的项目根目录下创建以下结构。我们将能力封装在 `skills` 中，通过 `agents` 定义角色，最后用 `commands` 作为快捷入口。

```text
.claude/
├── skills/                   # [能力层]
│   ├── backend-guard/        # 负责代码审计与规范检查
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── check_async.py  # (可选) 自动检测阻塞代码的脚本
│   ├── test-architect/       # 负责生成高质量测试代码
│   │   └── SKILL.md
│   └── mentor-brain/         # 负责知识归纳与复盘
│       └── SKILL.md
│
├── agents/                   # [角色层] (Subagents)
│   ├── qa.md                 # QA 验收专员
│   ├── sdet.md               # 测试开发专员
│   └── mentor.md             # 学习导师
│
└── commands/                 # [交互层]
    ├── audit.md              # -> 唤醒 QA
    ├── test.md               # -> 唤醒 SDET
    └── retro.md              # -> 唤醒 Mentor
```

---

### 🛠️ 2. Skills 配置 (The Engine)

这是 AI 的“大脑”和“手”。

#### Skill 1: Backend Guard (代码审计)
**文件**: `.claude/skills/backend-guard/SKILL.md`
```markdown
---
name: Backend Guard
description: Deep audit of FastAPI code focusing on Async safety and Pydantic usage.
---

# FastAPI Audit Expert

## Capabilities
You are an expert Backend Architect. You analyze code statically to find "Code Smells".

## 📋 Audit Checklist (Strict)
1.  **Async Blocking**: Check if `time.sleep` or sync I/O is used inside `async def`.
2.  **Dependency Injection**: Verify `Depends()` is used for `Session`.
3.  **Pydantic Models**: Ensure API `response_model` is NOT a raw SQLModel table class (should be a Schema).
4.  **Error Handling**: Check if `HTTPException` is raised properly.

## Action
If you see violations, output a report with: [CRITICAL], [WARNING], [SUGGESTION].
```

#### Skill 2: Test Architect (测试架构)
**文件**: `.claude/skills/test-architect/SKILL.md`
```markdown
---
name: Test Architect
description: Generates production-ready integration tests for FastAPI.
---

# Pytest Master

## 🧠 Knowledge Base
Always use `pytest-asyncio` and `httpx`. Use this specific fixture pattern:

	python
# Template for tests/conftest.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
	
## Instruction
When asked to "generate tests", analyze the `main.py` endpoints and write corresponding `test_*.py` files using the pattern above. NEVER use `TestClient` (sync).
```

#### Skill 3: Mentor Brain (知识复盘)
**文件**: `.claude/skills/mentor-brain/SKILL.md`
```markdown
---
name: Mentor Brain
description: Summarizes coding sessions into learning documents.
---

# Learning Mentor

## Task
Analyze the code changes and the user's recent activities.
Generate a `docs/learning_log_step3.md` file containing:
1.  **Key Concepts**: What technical concepts were implemented? (e.g., Dependency Injection, Async/Await).
2.  **Pitfalls**: What bugs were fixed?
3.  **Next Steps**: Suggest preparation for Deployment (Docker).
```

---

### 🤖 3. Subagents 配置 (The Personas)

这是 AI 的“身份”。通过 YAML 挂载对应的 Skill。

#### Agent 1: QA Bot
**文件**: `.claude/agents/qa.md`
```markdown
---
name: QA Bot
description: Strict code quality auditor.
model: claude-3-5-sonnet-20241022
skills: 
  - backend-guard
temperature: 0.1
---

# Role
You are a strict QA Engineer. Your job is to reject bad code.
When activated, immediately scan `main.py` and `crud.py` against the Audit Checklist.
```

#### Agent 2: SDET Bot
**文件**: `.claude/agents/sdet.md`
```markdown
---
name: SDET Bot
description: Automation test generator.
model: claude-3-5-sonnet-20241022
skills:
  - test-architect
---

# Role
You are an SDET. Your job is to ensure 100% test coverage.
When activated, look at the API endpoints and propose a test plan, then generate the code.
```

#### Agent 3: Mentor Bot
**文件**: `.claude/agents/mentor.md`
```markdown
---
name: Mentor Bot
description: Engineering Mentor.
model: claude-3-5-sonnet-20241022
skills:
  - mentor-brain
---

# Role
You are a supportive Mentor.
When activated, summarize the current project state and update the learning documentation.
```

---

### ⚡️ 4. Commands 配置 (The Triggers)

这是你的“快捷键”。

*   **`.claude/commands/audit.md`**:
    ```markdown
    ---
    description: Run QA Audit
    ---
    Act as the **QA Bot** (defined in agents/qa.md). Audit the current codebase strictly.
    ```

*   **`.claude/commands/test.md`**:
    ```markdown
    ---
    description: Generate Tests
    ---
    Act as the **SDET Bot** (defined in agents/sdet.md). Generate integration tests for all endpoints.
    ```

*   **`.claude/commands/retro.md`**:
    ```markdown
    ---
    description: Weekly Retrospective
    ---
    Act as the **Mentor Bot** (defined in agents/mentor.md). Perform a retrospective on Step 3.
    ```

---

### 🚀 5. 执行 SOP：周五下午的验收流程

现在，请按照以下顺序执行，完成 Step 3 的验收：

#### ✅ Step 1: 工程验收 (QA Phase)
在终端输入：
```bash
claude /audit
```
*   **预期结果**：Claude 会化身 QA，指出你代码中可能存在的 Async 阻塞问题或 Pydantic 模型混用问题。
*   **行动**：根据它的建议修复代码，直到它说 "Code looks clean"。

#### 🔗 Step 2: 智能联调 (Integration Phase)
在终端输入：
```bash
claude /test
```
*   **预期结果**：Claude 会化身 SDET，为你生成 `tests/conftest.py` 和 `tests/test_main.py`。
*   **行动**：运行 `pytest`。如果有报错，直接把错误贴给 Claude 让它修。确保所有测试通过。

#### 📚 Step 3: 学习归纳 (Learning Phase)
在终端输入：
```bash
claude /retro
```
*   **预期结果**：Claude 会化身导师，为你生成一份 `docs/learning_log_step3.md`。
*   **行动**：阅读这份文档，确认你掌握了 FastAPI 的核心概念。

---
