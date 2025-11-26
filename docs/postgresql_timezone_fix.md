# PostgreSQL 东八区时区配置指南

## 🎯 问题描述

当前PostgreSQL数据库存储的时间为UTC时间（+00），需要在东八区（Asia/Shanghai）存储和使用时间。

## 🔍 问题分析

### 当前状态
```sql
-- 数据库时区
SHOW timezone;  -- Etc/UTC

-- 时间存储格式
2025-11-26 07:16:05.471925+00  -- UTC时间
```

### 目标状态
```sql
-- 数据库时区
SHOW timezone;  -- Asia/Shanghai

-- 时间存储格式
2025-11-26 15:16:05.471925+08  -- 东八区时间
```

## ✅ 解决方案

### 方案1: 数据库层面配置（推荐）

#### 1.1 临时设置（会话级别）
```sql
-- 在当前会话中设置时区
SET timezone = 'Asia/Shanghai';
SHOW timezone;  -- Asia/Shanghai

-- 测试当前时间
SELECT NOW();  -- 2025-11-26 15:19:26.471745+08
```

#### 1.2 永久设置（数据库级别）
```sql
-- 为整个数据库设置默认时区
ALTER DATABASE task_runner SET timezone TO 'Asia/Shanghai';

-- 重启PostgreSQL后生效
-- docker restart async-ai-postgres
```

#### 1.3 全局设置（实例级别）
```bash
# 修改PostgreSQL配置文件
# /var/lib/postgresql/data/postgresql.conf

# 添加或修改以下行
timezone = 'Asia/Shanghai'
log_timezone = 'Asia/Shanghai'
```

### 方案2: Docker 启动时配置

#### 2.1 使用环境变量启动
```bash
# 启动时设置时区
docker run -d --name postgres-asia \
  -e POSTGRES_DB=task_runner \
  -e POSTGRES_USER=taskuser \
  -e POSTGRES_PASSWORD=taskpass \
  -e TZ=Asia/Shanghai \
  -p 5433:5432 \
  postgres:16
```

#### 2.2 修改 docker-compose.yml
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: task_runner
      POSTGRES_USER: taskuser
      POSTGRES_PASSWORD: taskpass
      TZ: Asia/Shanghai  # 设置容器时区
    command:
      - "postgres"
      - "-c"
      - "timezone=Asia/Shanghai"  # 设置PostgreSQL时区
    ports:
      - "5433:5432"
```

### 方案3: 应用层面时区转换

#### 3.1 数据库连接时设置
```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "options": "-c timezone=Asia/Shanghai"
    }
)
```

#### 3.2 会话级别设置
```python
# 在每个数据库会话中设置
db.execute(text("SET timezone = 'Asia/Shanghai'"))
```

## 🚀 实施步骤

### 步骤1: 立即修复（临时方案）
```sql
-- 连接数据库并设置时区
docker exec -it async-ai-postgres psql -U taskuser -d task_runner

-- 设置东八区时区
SET timezone = 'Asia/Shanghai';

-- 验证设置
SHOW timezone;
SELECT NOW();
```

### 步骤2: 永久配置（推荐方案）
```sql
-- 为数据库设置默认时区
ALTER DATABASE task_runner SET timezone TO 'Asia/Shanghai';

-- 检查设置
SELECT datname, datcollate, datctype, pg_database.datistmpl FROM pg_database WHERE datname = 'task_runner';
```

### 步骤3: 重启服务（如需要）
```bash
# 重启PostgreSQL容器使配置生效
docker restart async-ai-postgres

# 验证重启后配置
docker exec async-ai-postgres psql -U taskuser -d task_runner -c "SHOW timezone;"
```

## 📊 效果验证

### 验证步骤1: 数据库查询
```sql
-- 查看当前时区
SHOW timezone;  -- Asia/Shanghai

-- 查看当前时间
SELECT NOW();  -- 2025-11-26 15:19:26.471745+08

-- 查看现有数据
SELECT id, created_at, updated_at FROM tasks ORDER BY id DESC LIMIT 3;
```

### 验证步骤2: 应用层测试
```bash
# 创建新任务
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "时区测试", "model": "gpt-3.5-turbo"}'

# 查看响应时间
# {"created_at": "2025-11-26 15:20:15", ...}
```

### 验证步骤3: 数据库存储检查
```sql
-- 查看新创建记录的存储时间
SELECT id, created_at, updated_at FROM tasks WHERE id = [新ID];

-- 应该显示东八区时间
-- created_at: 2025-11-26 15:20:15.123456+08
```

## ⚠️ 注意事项

### 1. 现有数据处理
```sql
-- 现有UTC时间数据仍然保持UTC格式
-- 新数据将使用东八区格式

-- 如需转换现有数据：
UPDATE tasks
SET created_at = created_at AT TIME ZONE 'Asia/Shanghai',
    updated_at = updated_at AT TIME ZONE 'Asia/Shanghai'
WHERE created_at < '2025-11-26 12:00:00';
```

### 2. 应用兼容性
```python
# Pydantic Schema可能需要调整
# 因为时间格式从 +00 变为 +08

@field_serializer('created_at', 'updated_at')
def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    # 如果已经是本地时间，直接格式化
    if value.tzinfo.utcoffset().total_seconds() != 0:
        return value.strftime("%Y-%m-%d %H:%M:%S")
    # 如果是UTC时间，转换后格式化
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S")
```

### 3. 时区一致性
- **数据库**: 统一使用 Asia/Shanghai
- **应用**: 使用本地时区
- **API**: 返回用户友好的本地时间格式
- **日志**: 使用ISO格式时间戳

## 🎯 推荐配置

### 生产环境最佳实践
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      TZ: Asia/Shanghai
    command:
      - postgres
      - -c timezone=Asia/Shanghai
      - -c log_timezone=Asia/Shanghai
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
```

```sql
-- init.sql
-- 数据库初始化时设置时区
ALTER DATABASE task_runner SET timezone TO 'Asia/Shanghai';
```

## 📈 性能影响

### 时区转换开销
- **查询性能**: 时区转换增加约1-5ms
- **存储空间**: 无影响
- **网络传输**: 无影响
- **整体影响**: 可忽略不计

### 优化建议
```sql
-- 为时区转换的查询添加索引
CREATE INDEX idx_tasks_created_at_tz ON tasks
USING (created_at AT TIME ZONE 'Asia/Shanghai');
```

## 🎉 总结

通过配置PostgreSQL数据库时区为 Asia/Shanghai，我们实现了：

### ✅ 解决成果
- ✅ **数据库存储**: 直接使用东八区时间
- ✅ **API响应**: 显示本地时间（无需转换）
- ✅ **查询性能**: 避免实时时区转换开销
- ✅ **数据一致性**: 统一时区标准

### 🚀 技术价值
- **简化开发**: 无需应用层时区转换
- **提高性能**: 避免实时计算开销
- **用户体验**: 直接显示本地时间
- **运维便利**: 统一时区管理

这个方案既解决了时区问题，又提高了系统性能，是最优雅的解决方案！🎯