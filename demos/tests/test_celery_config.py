"""
Celery配置测试脚本
用于验证Redis连接和Celery任务是否正常工作
"""
import time
from app.worker.app import celery_app
from app.worker.tasks.demo_tasks import (
    simple_calculation,
    send_notification_email,
    process_file_upload
)
from app.worker.tasks.ai_tasks import run_ai_text_generation


def test_redis_connection():
    """测试Redis连接"""
    print("🔗 测试Redis连接...")
    try:
        # 测试Redis连接
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if stats:
            print("✅ Redis连接成功")
            return True
        else:
            print("⚠️  Redis连接成功，但没有活跃的Worker")
            return True

    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False


def test_simple_task():
    """测试简单计算任务"""
    print("\n🧮 测试简单计算任务...")
    try:
        # 发送任务
        result = simple_calculation.delay(10, 20, "add")
        print(f"📤 任务已发送: {result.id}")

        # 等待结果
        for i in range(10):
            if result.ready():
                print(f"✅ 任务完成: {result.get()}")
                return True
            print(f"⏳ 等待任务完成... ({i+1}/10)")
            time.sleep(1)

        print("⚠️  任务超时")
        return False

    except Exception as e:
        print(f"❌ 任务执行失败: {e}")
        return False


def test_email_task():
    """测试邮件发送任务"""
    print("\n📧 测试邮件发送任务...")
    try:
        # 发送邮件任务
        result = send_notification_email.delay(
            recipient="test@example.com",
            subject="测试邮件",
            message="这是一封测试邮件"
        )
        print(f"📤 邮件任务已发送: {result.id}")

        # 等待结果
        for i in range(15):
            if result.ready():
                email_result = result.get()
                print(f"✅ 邮件任务完成: {email_result}")
                return True
            print(f"⏳ 等待邮件发送... ({i+1}/15)")
            time.sleep(1)

        print("⚠️  邮件任务超时")
        return False

    except Exception as e:
        print(f"❌ 邮件任务失败: {e}")
        return False


def test_ai_task():
    """测试AI文本生成任务"""
    print("\n🤖 测试AI文本生成任务...")
    try:
        # 首先需要创建一个数据库任务记录
        from app.database import get_db_session
        from app.models import Task, TaskStatus
        from app.schemas import TaskCreate
        import uuid

        # 创建数据库任务
        task_id = str(uuid.uuid4())
        async def create_db_task():
            async with get_db_session() as db:
                db_task = Task(
                    id=task_id,
                    prompt="今天天气怎么样？",
                    model="gpt-3.5-turbo",
                    status=TaskStatus.PENDING
                )
                db.add(db_task)
                await db.commit()
                await db.refresh(db_task)
                return db_task

        import asyncio
        db_task = asyncio.run(create_db_task())
        print(f"📝 数据库任务已创建: {db_task.id}")

        # 发送AI任务
        result = run_ai_text_generation.delay(
            task_id=task_id,
            prompt="今天天气怎么样？",
            model="gpt-3.5-turbo"
        )
        print(f"📤 AI任务已发送: {result.id}")

        # 监控任务进度（更长时间）
        for i in range(60):  # 最多等待60秒
            if result.ready():
                ai_result = result.get()
                print(f"✅ AI任务完成: {ai_result}")
                return True
            else:
                # 检查任务进度
                meta = result.info
                if meta and 'progress' in meta:
                    print(f"⏳ AI处理进度: {meta['progress']}% - {meta.get('status', '')}")
                else:
                    print(f"⏳ AI任务处理中... ({i+1}/60)")
                time.sleep(1)

        print("⚠️  AI任务超时")
        return False

    except Exception as e:
        print(f"❌ AI任务失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始Celery配置测试\n")

    # 测试连接
    if not test_redis_connection():
        print("❌ Redis连接测试失败，请检查Redis服务")
        return

    print("\n" + "="*50)
    print("注意: 以下测试需要Celery Worker运行")
    print("请在另一个终端运行:")
    print("celery -A app.worker.celery_app worker --loglevel=info")
    print("="*50 + "\n")

    # 测试各项功能
    test_results = []

    # 简单任务测试
    test_results.append(("简单计算任务", test_simple_task()))

    # 邮件任务测试
    test_results.append(("邮件发送任务", test_email_task()))

    # AI任务测试
    test_results.append(("AI文本生成任务", test_ai_task()))

    # 总结
    print("\n" + "="*50)
    print("📊 测试结果总结")
    print("="*50)

    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:20} : {status}")

    all_passed = all(result[1] for result in test_results)
    if all_passed:
        print(f"\n🎉 所有测试通过！Celery配置正常")
    else:
        print(f"\n⚠️  部分测试失败，请检查配置和Worker状态")


if __name__ == "__main__":
    main()