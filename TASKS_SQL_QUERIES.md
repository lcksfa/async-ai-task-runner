# Tasks 表 SQL 查询示例

本文档提供从 tasks 表中获取最新数据的各种 SQL 查询示例。

## 表结构回顾

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    prompt TEXT NOT NULL,
    model VARCHAR(100),
    provider VARCHAR(50),
    priority INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

## 1. 获取最新的任务记录

### 1.1 获取最新的 N 条任务（按创建时间倒序）
```sql
-- 获取最新的 10 条任务
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    LEFT(result, 100) || '...' AS result_preview,
    created_at,
    updated_at
FROM tasks
ORDER BY created_at DESC
LIMIT 10;
```

### 1.2 获取最新的已完成任务
```sql
-- 获取最新的 5 条已完成任务
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    LEFT(result, 150) AS result_preview,
    created_at,
    updated_at
FROM tasks
WHERE status = 'COMPLETED'
ORDER BY updated_at DESC
LIMIT 5;
```

### 1.3 获取最新的处理中任务
```sql
-- 获取正在处理的任务
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    created_at,
    updated_at,
    EXTRACT(EPOCH FROM (updated_at - created_at)) AS processing_duration_seconds
FROM tasks
WHERE status = 'PROCESSING'
ORDER BY created_at DESC;
```

## 2. 按时间范围获取最新数据

### 2.1 获取最近 24 小时的任务
```sql
-- 获取最近 24 小时内的所有任务
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    created_at,
    updated_at,
    CASE
        WHEN status = 'COMPLETED' THEN
            EXTRACT(EPOCH FROM (updated_at - created_at))
        ELSE NULL
    END AS processing_time_seconds
FROM tasks
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### 2.2 获取今天的任务
```sql
-- 获取今天创建的所有任务
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    created_at,
    updated_at
FROM tasks
WHERE DATE(created_at) = DATE(NOW())
ORDER BY created_at DESC;
```

### 2.3 获取本周的任务
```sql
-- 获取本周创建的任务
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    created_at,
    updated_at
FROM tasks
WHERE created_at >= DATE_TRUNC('week', NOW())
ORDER BY created_at DESC;
```

## 3. 按状态分组的最新统计

### 3.1 任务状态统计
```sql
-- 获取各种状态的任务数量
SELECT
    status,
    COUNT(*) as task_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM tasks), 2) as percentage
FROM tasks
GROUP BY status
ORDER BY task_count DESC;
```

### 3.2 按模型和状态分组统计
```sql
-- 各模型的任务完成情况
SELECT
    model,
    status,
    COUNT(*) as task_count
FROM tasks
WHERE model IS NOT NULL
GROUP BY model, status
ORDER BY model, status;
```

### 3.3 按提供商和状态分组统计
```sql
-- 各AI提供商的任务完成情况
SELECT
    provider,
    status,
    COUNT(*) as task_count,
    ROUND(AVG(
        CASE
            WHEN status = 'COMPLETED' THEN
                EXTRACT(EPOCH FROM (updated_at - created_at))
            ELSE NULL
        END
    ), 2) as avg_processing_time_seconds
FROM tasks
WHERE provider IS NOT NULL
GROUP BY provider, status
ORDER BY provider, status;
```

## 4. 性能和监控相关查询

### 4.1 获取处理时间最长的任务
```sql
-- 获取处理时间最长的 10 个已完成任务
SELECT
    id,
    model,
    provider,
    EXTRACT(EPOCH FROM (updated_at - created_at)) AS processing_time_seconds,
    ROUND(
        EXTRACT(EPOCH FROM (updated_at - created_at)) / 60, 2
    ) AS processing_time_minutes,
    created_at,
    updated_at
FROM tasks
WHERE status = 'COMPLETED'
  AND updated_at > created_at
ORDER BY processing_time_seconds DESC
LIMIT 10;
```

### 4.2 获取优先级高的待处理任务
```sql
-- 获取优先级最高的待处理任务
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    created_at,
    updated_at
FROM tasks
WHERE status = 'PENDING'
ORDER BY priority DESC, created_at ASC
LIMIT 10;
```

### 4.3 平均处理时间分析
```sql
-- 按模型分析平均处理时间
SELECT
    model,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_tasks,
    ROUND(
        AVG(
            CASE
                WHEN status = 'COMPLETED' THEN
                    EXTRACT(EPOCH FROM (updated_at - created_at))
                ELSE NULL
            END
        ), 2
    ) as avg_processing_time_seconds,
    ROUND(
        AVG(
            CASE
                WHEN status = 'COMPLETED' THEN
                    EXTRACT(EPOCH FROM (updated_at - created_at)) / 60
                ELSE NULL
            END
        ), 2
    ) as avg_processing_time_minutes
FROM tasks
WHERE model IS NOT NULL
GROUP BY model
ORDER BY total_tasks DESC;
```

## 5. 复杂查询示例

### 5.1 获取最新任务的详细信息
```sql
-- 获取最新任务的完整信息，包含处理时间计算
WITH latest_tasks AS (
    SELECT
        id,
        prompt,
        model,
        provider,
        priority,
        status,
        result,
        created_at,
        updated_at,
        ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
    FROM tasks
)
SELECT
    id,
    prompt,
    model,
    provider,
    priority,
    status,
    LEFT(result, 200) AS result_preview,
    created_at,
    updated_at,
    CASE
        WHEN status IN ('COMPLETED', 'FAILED') AND updated_at > created_at THEN
            EXTRACT(EPOCH FROM (updated_at - created_at))
        ELSE NULL
    END AS processing_duration_seconds,
    CASE
        WHEN updated_at > created_at THEN
            updated_at::time - created_at::time
        ELSE NULL
    END AS processing_duration_time
FROM latest_tasks
WHERE rn <= 20  -- 最新的 20 条记录
ORDER BY created_at DESC;
```

### 5.2 获取失败任务的分析
```sql
-- 分析失败任务的常见模式
SELECT
    id,
    model,
    provider,
    priority,
    LEFT(result, 100) AS error_preview,
    created_at,
    updated_at
FROM tasks
WHERE status = 'FAILED'
ORDER BY created_at DESC
LIMIT 20;
```

### 5.3 按小时统计任务创建情况
```sql
-- 按小时统计任务创建数量（最近24小时）
SELECT
    EXTRACT(HOUR FROM created_at) as hour_of_day,
    DATE(created_at) as date,
    COUNT(*) as task_count,
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed_count
FROM tasks
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE(created_at), EXTRACT(HOUR FROM created_at)
ORDER BY date, hour_of_day;
```

## 6. 索引优化建议

为了提高查询性能，建议创建以下索引：

```sql
-- 按创建时间查询的索引
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);

-- 按状态查询的索引
CREATE INDEX idx_tasks_status ON tasks(status);

-- 按模型查询的索引
CREATE INDEX idx_tasks_model ON tasks(model);

-- 按提供商查询的索引
CREATE INDEX idx_tasks_provider ON tasks(provider);

-- 复合索引（状态 + 创建时间）
CREATE INDEX idx_tasks_status_created_at ON tasks(status, created_at DESC);

-- 复合索引（模型 + 状态）
CREATE INDEX idx_tasks_model_status ON tasks(model, status);
```

## 使用提示

1. **选择合适的查询**: 根据你的具体需求选择相应的查询
2. **限制结果集**: 使用 LIMIT 限制返回的记录数量
3. **索引优化**: 为常用查询字段创建索引
4. **时间格式**: 注意时区处理，使用 `AT TIME ZONE` 类型
5. **结果预览**: 使用 `LEFT()` 函数预览长文本字段

这些查询涵盖了从简单到复杂的各种场景，可以根据实际需求进行调整和组合。