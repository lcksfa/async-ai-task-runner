"""
演示任务模块
用于测试和学习Celery任务的基本功能
"""
import time
import random
from datetime import datetime
from app.worker.app import celery_app


@celery_app.task(name="simple_calculation")
def simple_calculation(a: int, b: int, operation: str = "add"):
    """
    简单的数学计算任务
    用于测试Celery基本功能
    """
    print(f"🔢 开始计算: {a} {operation} {b}")

    # 模拟计算时间
    time.sleep(random.uniform(1, 3))

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("除数不能为零")
        result = a / b
    else:
        raise ValueError(f"不支持的操作: {operation}")

    print(f"✅ 计算结果: {result}")
    return {
        "operation": f"{a} {operation} {b}",
        "result": result,
        "timestamp": datetime.now().isoformat()
    }


@celery_app.task(name="send_notification_email")
def send_notification_email(recipient: str, subject: str, message: str):
    """
    发送通知邮件的演示任务
    """
    print(f"📧 开始发送邮件...")
    print(f"👤 收件人: {recipient}")
    print(f"📋 主题: {subject}")
    print(f"📝 内容: {message[:50]}...")

    # 模拟邮件发送时间
    time.sleep(random.uniform(2, 5))

    # 模拟发送结果
    success_rate = 0.95
    if random.random() < success_rate:
        print(f"✅ 邮件发送成功: {recipient}")
        return {
            "status": "success",
            "recipient": recipient,
            "sent_at": datetime.now().isoformat(),
            "message_id": f"msg_{random.randint(10000, 99999)}"
        }
    else:
        print(f"❌ 邮件发送失败: {recipient}")
        raise Exception("邮件服务器暂时不可用")


@celery_app.task(name="process_file_upload")
def process_file_upload(file_path: str, processing_options: dict):
    """
    文件上传处理的演示任务
    """
    print(f"📁 开始处理文件: {file_path}")
    print(f"⚙️ 处理选项: {processing_options}")

    # 模拟文件处理阶段
    stages = [
        ("验证文件格式", 2),
        ("病毒扫描", 3),
        ("内容分析", 5),
        ("生成缩略图", 2),
        ("保存到云存储", 4)
    ]

    total_time = sum(stage[1] for stage in stages)
    elapsed_time = 0

    for stage_name, stage_time in stages:
        print(f"🔄 {stage_name}...")
        time.sleep(stage_time)
        elapsed_time += stage_time
        progress = int((elapsed_time / total_time) * 100)
        print(f"📊 进度: {progress}%")

    # 模拟处理结果
    result = {
        "file_path": file_path,
        "status": "completed",
        "file_size": "2.5MB",
        "file_type": "image/jpeg",
        "processing_time": f"{total_time}s",
        "thumbnail_url": f"/thumbnails/{file_path.split('/')[-1]}",
        "processed_at": datetime.now().isoformat()
    }

    print(f"✅ 文件处理完成: {result}")
    return result


@celery_app.task(name="generate_report")
def generate_report(report_type: str, data_source: str, format_type: str = "pdf"):
    """
    生成报告的演示任务
    """
    print(f"📊 开始生成报告...")
    print(f"📋 报告类型: {report_type}")
    print(f"💾 数据源: {data_source}")
    print(f"📄 格式: {format_type}")

    # 模拟报告生成时间
    time.sleep(random.uniform(5, 10))

    # 模拟报告结果
    result = {
        "report_id": f"rpt_{random.randint(10000, 99999)}",
        "type": report_type,
        "format": format_type,
        "pages": random.randint(10, 50),
        "file_size": f"{random.uniform(0.5, 5.0):.1f}MB",
        "download_url": f"/reports/rpt_{random.randint(10000, 99999)}.{format_type}",
        "generated_at": datetime.now().isoformat()
    }

    print(f"✅ 报告生成完成: {result}")
    return result


# 错误处理和重试演示
@celery_app.task(bind=True, name="unreliable_task", max_retries=3)
def unreliable_task(self, should_fail: bool = False):
    """
    演示错误处理和重试机制的任务
    """
    try:
        if should_fail and random.random() < 0.7:  # 70%概率失败
            raise Exception("任务随机失败（演示用）")

        print(f"✅ 不可靠任务执行成功")
        return {"status": "success", "attempt": self.request.retries + 1}

    except Exception as exc:
        print(f"❌ 任务失败，尝试重试... (第{self.request.retries + 1}次)")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)