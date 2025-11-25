#!/usr/bin/env python3
"""
Pydantic 核心概念演示

这个脚本演示了 Pydantic 的主要功能，与 FastAPI 无关，
专注于理解 Pydantic 本身的概念。

运行: uv run python pydantic_concepts_demo.py
"""

from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json

# ====== 1. 基础模型定义 ======

class TaskStatus(str, Enum):
    """枚举类型 - 限制字段的可能值"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TaskModel(BaseModel):
    """基础任务模型"""
    model_config = ConfigDict(
        validate_by_name=True,  # 替代 allow_population_by_field_name
    )

    title: str                          # 必填字段
    description: Optional[str] = None   # 可选字段
    priority: int = 1                  # 带默认值的字段
    tags: List[str] = []               # 列表字段
    status: TaskStatus = TaskStatus.PENDING  # 枚举字段
    created_at: datetime = Field(default_factory=datetime.now)  # 动态默认值

def demo_basic_model():
    """演示基础模型功能"""
    print("=" * 60)
    print("🔧 基础模型演示")
    print("=" * 60)

    # 1. 创建有效实例
    print("\n1. 创建有效任务实例:")
    task = TaskModel(
        title="学习 FastAPI",
        description="通过实践项目学习 FastAPI 框架",
        priority=5,
        tags=["学习", "编程", "Python"],
        status=TaskStatus.PROCESSING
    )
    print(f"✅ 任务创建成功: {task.title}")
    print(f"📅 创建时间: {task.created_at}")

    # 2. 使用默认值
    print("\n2. 使用默认值:")
    simple_task = TaskModel(title="简单任务")
    print(f"✅ 简单任务 - 优先级: {simple_task.priority}, 状态: {simple_task.status}")

    # 3. 模型转换为字典
    print("\n3. 模型转字典:")
    task_dict = task.model_dump()
    print(f"📋 字典格式: {json.dumps(task_dict, indent=2, ensure_ascii=False, default=str)}")

    # 4. 模型转换为JSON
    print("\n4. 模型转JSON:")
    task_json = task.model_dump_json()
    print(f"📄 JSON格式: {task_json}")

    # 5. 从字典创建模型
    print("\n5. 从字典创建模型:")
    task_data = {
        "title": "从字典创建",
        "priority": 3,
        "tags": ["演示"]
    }
    # ** 在这里表示将字典的键值对展开为关键字参数传递给模型构造函数
    task_from_dict = TaskModel(**task_data)
    print(f"✅ 从字典创建成功: {task_from_dict.title}")

    return task

# ====== 2. 字段验证演示 ======

class ValidatedTask(BaseModel):
    """带验证的任务模型"""
    title: str = Field(..., min_length=1, max_length=100, description="任务标题")
    priority: int = Field(..., ge=1, le=10, description="优先级1-10")
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """自定义验证器"""
        if not v.strip():
            raise ValueError('标题不能为空或只有空格')
        if '快速' in v and '轻松' in v:
            raise ValueError('标题不能同时包含"快速"和"轻松"')
        return v.strip()

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """优先级验证"""
        if v > 8:
            print(f"⚠️  警告: 优先级 {v} 很高，请谨慎使用")
        return v

def demo_field_validation():
    """演示字段验证"""
    print("\n" + "=" * 60)
    print("✅ 字段验证演示")
    print("=" * 60)

    # 1. 有效数据
    print("\n1. 有效数据验证:")
    try:
        valid_task = ValidatedTask(
            title="完成项目文档",
            priority=5,
            email="user@example.com"
        )
        print(f"✅ 验证通过: {valid_task.title}")
    except ValidationError as e:
        print(f"❌ 验证失败: {e}")

    # 2. 无效数据 - 标题太短
    print("\n2. 标题太短:")
    try:
        ValidatedTask(
            title="",
            priority=5,
            email="user@example.com"
        )
    except ValidationError as e:
        print(f"❌ 预期错误 - 标题太短")
        for error in e.errors():
            print(f"   字段: {error['loc']}, 错误: {error['msg']}")

    # 3. 无效数据 - 优先级超出范围
    print("\n3. 优先级超出范围:")
    try:
        ValidatedTask(
            title="测试任务",
            priority=15,
            email="user@example.com"
        )
    except ValidationError as e:
        print(f"❌ 预期错误 - 优先级超出范围")
        for error in e.errors():
            print(f"   字段: {error['loc']}, 错误: {error['msg']}")

    # 4. 无效数据 - 邮箱格式错误
    print("\n4. 邮箱格式错误:")
    try:
        ValidatedTask(
            title="测试任务",
            priority=5,
            email="invalid-email"
        )
    except ValidationError as e:
        print(f"❌ 预期错误 - 邮箱格式错误")
        for error in e.errors():
            print(f"   字段: {error['loc']}, 错误: {error['msg']}")

    # 5. 自定义验证器错误
    print("\n5. 自定义验证器错误:")
    try:
        ValidatedTask(
            title="快速轻松完成任务",
            priority=5,
            email="user@example.com"
        )
    except ValidationError as e:
        print(f"❌ 预期错误 - 自定义验证器")
        for error in e.errors():
            print(f"   字段: {error['loc']}, 错误: {error['msg']}")

# ====== 3. 模型继承和组合 ======

class BaseTaskModel(BaseModel):
    """基础模型类"""
    id: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

class User:
    """用户模型（不继承 BaseModel）"""
    def __init__(self, name: str, email: str, role: str = "user"):
        self.name = name
        self.email = email
        self.role = role

class TaskWithUser(BaseModel):
    """包含用户信息的任务"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    task: TaskModel
    assigned_user: User
    metadata: Dict[str, Any] = {}

def demo_model_composition():
    """演示模型组合"""
    print("\n" + "=" * 60)
    print("🔗 模型组合演示")
    print("=" * 60)

    # 创建复合模型
    user = User(name="张三", email="zhangsan@example.com", role="developer")
    task = TaskModel(
        title="开发新功能",
        description="实现用户认证功能",
        priority=8,
        tags=["开发", "认证"]
    )

    composite = TaskWithUser(
        task=task,
        assigned_user=user,
        metadata={"project": "FastAPI Demo", "deadline": "2024-12-31"}
    )

    print(f"✅ 复合模型创建成功")
    print(f"👤 分配用户: {composite.assigned_user.name} ({composite.assigned_user.role})")
    print(f"📋 任务标题: {composite.task.title}")
    print(f"📊 项目: {composite.metadata.get('project')}")

# ====== 4. 数据转换和解析 ======

class AdvancedTask(BaseModel):
    """高级任务模型 - 演示数据转换"""
    title: str
    duration_hours: float = Field(alias="duration")  # 字段别名
    tags_comma_separated: List[str] = Field(alias="tags")  # 数据转换

    @field_validator('tags_comma_separated', mode='before')
    @classmethod
    def parse_tags(cls, v):
        """预验证 - 解析逗号分隔的标签"""
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        elif isinstance(v, list):
            return [str(tag).strip() for tag in v]
        return v

def demo_data_transformation():
    """演示数据转换"""
    print("\n" + "=" * 60)
    print("🔄 数据转换演示")
    print("=" * 60)

    # 使用字段别名和数据转换
    raw_data = {
        "title": "数据分析项目",
        "duration": "2.5",  # 字符串会自动转换为float
        "tags": "Python,数据分析,可视化"  # 逗号分隔的字符串
    }

    task = AdvancedTask(**raw_data)
    print(f"✅ 数据转换成功")
    print(f"📋 标题: {task.title}")
    print(f"⏱️  时长: {task.duration_hours} 小时")
    print(f"🏷️  标签: {task.tags_comma_separated}")

    # 导出时使用别名
    print(f"\n📄 导出数据（使用别名）:")
    exported = task.model_dump(by_alias=True)
    print(json.dumps(exported, indent=2, ensure_ascii=False))

# ====== 5. 实际应用场景演示 ======

class APITask(BaseModel):
    """API任务模型 - 模拟实际应用"""
    model_config = ConfigDict(
        # 字段别名映射
        populate_by_name=True,
        # 模式示例
        json_schema_extra={
            "example": {
                "title": "完成API文档",
                "description": "为新的API端点编写详细文档",
                "priority": 7,
                "assignee_email": "writer@example.com"
            }
        }
    )

    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: int = Field(1, ge=1, le=10, description="优先级(1-10)")
    assignee_email: Optional[str] = Field(None,
                                          pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                                          alias="assigneeEmail")

def demo_real_world_scenario():
    """演示实际应用场景"""
    print("\n" + "=" * 60)
    print("🌍 实际应用场景演示")
    print("=" * 60)

    # 1. API请求数据验证
    print("\n1. 模拟API请求验证:")
    api_request_data = {
        "title": "用户认证系统",
        "description": "实现JWT认证和用户管理",
        "priority": 9,
        "assigneeEmail": "security@example.com"
    }

    try:
        api_task = APITask(**api_request_data)
        print(f"✅ API请求数据验证通过")
        print(f"📋 任务: {api_task.title}")
        print(f"👤 分配给: {api_task.assignee_email}")

        # 生成JSON Schema（用于前端验证）
        schema = APITask.model_json_schema()
        print(f"\n📋 生成的JSON Schema字段数量: {len(schema.get('properties', {}))}")

    except ValidationError as e:
        print(f"❌ API请求验证失败")
        for error in e.errors():
            print(f"   {error}")

# ====== 6. 性能比较演示 ======

def demo_performance():
    """演示性能比较"""
    print("\n" + "=" * 60)
    print("⚡ 性能演示")
    print("=" * 60)

    import time

    # 准备测试数据
    test_data = [
        {
            "title": f"任务 {i}",
            "description": f"这是第 {i} 个任务的描述",
            "priority": (i % 10) + 1,
            "assigneeEmail": f"user{i}@example.com"
        }
        for i in range(1000)
    ]

    # 测试Pydantic验证性能
    start_time = time.time()
    validated_tasks = []
    for data in test_data:
        try:
            task = APITask(**data)
            validated_tasks.append(task)
        except ValidationError:
            pass
    pydantic_time = time.time() - start_time

    # 测试纯字典操作（无验证）
    start_time = time.time()
    dict_tasks = []
    for data in test_data:
        dict_tasks.append(data)
    dict_time = time.time() - start_time

    print(f"📊 性能比较结果:")
    print(f"   🔍 Pydantic验证: {pydantic_time:.4f}秒")
    print(f"   📝 纯字典操作: {dict_time:.4f}秒")
    print(f"   📈 性能比率: {pydantic_time/dict_time:.2f}x")
    print(f"   ✅ 验证通过的任务: {len(validated_tasks)}/{len(test_data)}")
    print(f"\n💡 结论: Pydantic提供类型安全，性能开销很小")

# ====== 主函数 ======

def main():
    """主函数 - 运行所有演示"""
    print("🚀 Pydantic 核心概念全面演示")
    print("=" * 80)

    # 1. 基础模型
    demo_basic_model()

    # 2. 字段验证
    demo_field_validation()

    # 3. 模型组合
    demo_model_composition()

    # 4. 数据转换
    demo_data_transformation()

    # 5. 实际应用
    demo_real_world_scenario()

    # 6. 性能演示
    demo_performance()

    print("\n" + "=" * 80)
    print("🎉 Pydantic 演示完成!")
    print("💡 关键要点:")
    print("   - 类型安全: 编译时和运行时类型检查")
    print("   - 自动验证: 字段约束和自定义验证器")
    print("   - 数据转换: 自动类型转换和数据清理")
    print("   - 文档生成: 自动生成JSON Schema")
    print("   - 性能优秀: 高效的验证和序列化")
    print("   - 易于使用: 简洁的API和丰富的功能")

if __name__ == "__main__":
    main()