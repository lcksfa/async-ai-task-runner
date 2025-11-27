# 🔬 Async AI Task Runner 详细集成测试方案

## 📋 测试准备清单

### 🔧 环境检查
- [ ] 所有 Docker 容器运行正常 (`docker-compose ps`)
- [ ] FastAPI 服务响应正常 (`curl http://localhost:8000/api/v1/health`)
- [ ] PostgreSQL 连接问题已解决
- [ ] Redis 服务正常 (`redis-cli ping`)
- [ ] Flower 监控界面可访问 (`http://localhost:5555`)
- [ ] 环境变量配置正确 (.env 文件)

### 📝 测试工具准备
- [ ] Postman 或 Insomnia (API 测试)
- [ ] curl 命令行工具
- [ ] Docker 命令行工具
- [ ] 数据库客户端 (pgAdmin 或 psql)
- [ ] 测试数据准备

---

## 🚀 阶段一：基础连接与功能验证测试

### 1.1 服务健康检查测试

**测试步骤：**

```bash
# 1. 测试 FastAPI 健康检查
curl -X GET "http://localhost:8000/api/v1/health" \
  -H "accept: application/json"

# 预期结果：
{"status":"healthy","app_name":"Async AI Task Runner","version":"0.1.0","timestamp":"..."}

# 2. 测试服务根路径
curl -X GET "http://localhost:8000/"

# 3. 测试 OpenAPI 文档
curl -X GET "http://localhost:8000/docs"

# 4. 检查数据库连接
curl -X GET "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json"
```

**验收标准：**
- ✅ 所有接口返回正确的 HTTP 状态码
- ✅ 健康检查包含应用信息和时间戳
- ✅ OpenAPI 文档可正常访问

### 1.2 数据库连接验证

```bash
# 1. 直接连接 PostgreSQL
docker exec -it async_ai_postgres psql -U postgres -d async_ai_task_runner -c "SELECT 1;"

# 2. 测试 Redis 连接
docker exec -it async_ai_redis redis-cli ping

# 3. 检查数据库表结构
docker exec -it async_ai_postgres psql -U postgres -d async_ai_task_runner -c "\d tasks"
```

---

## 📝 阶段二：任务创建与执行流程测试

### 2.1 基础任务创建测试

**测试用例 1：创建简单文本生成任务**

```bash
# 测试数据
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "请用一句话介绍人工智能",
    "model": "deepseek-chat",
    "priority": 1
  }'

# 预期响应格式：
{
  "id": 1,
  "prompt": "请用一句话介绍人工智能",
  "model": "deepseek-chat",
  "status": "PENDING",
  "priority": 1,
  "created_at": "2025-11-27T10:00:00Z",
  "updated_at": "2025-11-27T10:00:00Z"
}
```

**测试用例 2：创建带有优先级的任务**

```bash
# 高优先级任务
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "紧急：计算斐波那契数列第10项",
    "model": "deepseek-chat",
    "priority": 10
  }'

# 低优先级任务
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "普通：讲一个关于编程的笑话",
    "model": "deepseek-chat",
    "priority": 1
  }'
```

### 2.2 任务状态追踪测试

**测试步骤：**

```bash
# 1. 创建任务并记录 ID
TASK_ID=$(curl -s -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "测试任务", "model": "deepseek-chat", "priority": 1}' | \
  jq -r '.id')

# 2. 轮询任务状态
for i in {1..30}; do
  echo "检查第 $i 次..."
  curl -X GET "http://localhost:8000/api/v1/tasks/$TASK_ID" \
    -H "accept: application/json" | jq -r '.status'
  sleep 2
done
```

**预期状态流转：**
1. `PENDING` → `PROCESSING` → `COMPLETED`
2. 或 `PENDING` → `FAILED`

### 2.3 批量任务创建测试

```bash
# 创建多个任务测试并发处理
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/v1/tasks" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"批量任务 $i：请解释 $i 的含义\",
      \"model\": \"deepseek-chat\",
      \"priority\": $((i % 3 + 1))
    }" &
done

wait  # 等待所有后台任务完成
```

### 2.4 任务列表查询测试

```bash
# 1. 获取所有任务
curl -X GET "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json"

# 2. 按状态过滤
curl -X GET "http://localhost:8000/api/v1/tasks?status=PENDING" \
  -H "accept: application/json"

# 3. 按优先级过滤
curl -X GET "http://localhost:8000/api/v1/tasks?priority=10" \
  -H "accept: application/json"

# 4. 分页测试
curl -X GET "http://localhost:8000/api/v1/tasks?skip=0&limit=10" \
  -H "accept: application/json"
```

---

## 🚨 阶段三：错误处理与边界情况测试

### 3.1 输入验证测试

**测试用例 1：无效的请求体**

```bash
# 1. 空请求体
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d ''

# 预期：HTTP 422 Unprocessable Entity

# 2. 缺少必需字段
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "测试任务"}'

# 3. 无效的数据类型
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "测试任务",
    "model": "deepseek-chat",
    "priority": "high"  # 应该是数字
  }'

# 4. 超长输入
curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "'$(printf 'a'%.0s {1..10000})'",
    "model": "deepseek-chat",
    "priority": 1
  }'
```

### 3.2 任务 ID 测试

```bash
# 1. 不存在的任务 ID
curl -X GET "http://localhost:8000/api/v1/tasks/999999" \
  -H "accept: application/json"

# 预期：HTTP 404 Not Found

# 2. 无效的任务 ID 格式
curl -X GET "http://localhost:8000/api/v1/tasks/abc" \
  -H "accept: application/json"

# 3. 负数 ID
curl -X GET "http://localhost:8000/api/v1/tasks/-1" \
  -H "accept: application/json"

# 4. 零值 ID
curl -X GET "http://localhost:8000/api/v1/tasks/0" \
  -H "accept: application/json"
```

### 3.3 HTTP 方法测试

```bash
# 1. 不支持的 HTTP 方法
curl -X DELETE "http://localhost:8000/api/v1/tasks/1" \
  -H "accept: application/json"

curl -X PUT "http://localhost:8000/api/v1/tasks/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"status": "COMPLETED"}'

# 2. 错误的端点
curl -X GET "http://localhost:8000/api/v1/task" \
  -H "accept: application/json"

curl -X POST "http://localhost:8000/api/v1/invalid" \
  -H "accept: application/json"
```

### 3.4 并发与竞争条件测试

```bash
# 创建相同内容的任务，测试去重
for i in {1..3}; do
  curl -X POST "http://localhost:8000/api/v1/tasks" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "重复测试任务",
      "model": "deepseek-chat",
      "priority": 1
    }' &
done
wait
```

---

## ⚡ 阶段四：性能与负载测试

### 4.1 响应时间测试

**基准测试：**

```bash
# 1. 健康检查响应时间
time curl -X GET "http://localhost:8000/api/v1/health"

# 2. 任务创建响应时间
time curl -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "性能测试", "model": "deepseek-chat", "priority": 1}'

# 3. 任务查询响应时间
time curl -X GET "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json"
```

**验收标准：**
- ✅ 健康检查 < 50ms
- ✅ 任务创建 < 200ms
- ✅ 任务查询 < 300ms

### 4.2 负载测试

**轻负载测试 (10个并发任务)：**

```bash
# 创建测试脚本
cat > load_test_light.sh << 'EOF'
#!/bin/bash
echo "开始轻负载测试..."
start_time=$(date +%s)

for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/tasks" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"负载测试任务 $i\",
      \"model\": \"deepseek-chat\",
      \"priority\": $((i % 5 + 1))
    }" &
done

wait
end_time=$(date +%s)
duration=$((end_time - start_time))
echo "轻负载测试完成，耗时: ${duration}秒"
EOF

chmod +x load_test_light.sh
./load_test_light.sh
```

**中负载测试 (50个并发任务)：**

使用 Python 脚本进行更精确的负载测试（参考 `scripts/load-test-medium.py`）

### 4.3 系统资源监控

```bash
# 监控系统资源使用
docker stats --no-stream async_ai_web async_ai_worker async_ai_postgres async_ai_redis

# 监控容器日志
docker logs -f async_ai_web &
docker logs -f async_ai_worker &
```

---

## 🗄️ 阶段五：数据一致性测试

### 5.1 数据库状态验证

**测试步骤：**

```bash
# 1. 直接查询数据库验证数据一致性
docker exec -it async_ai_postgres psql -U postgres -d async_ai_task_runner -c "
SELECT
    status,
    COUNT(*) as task_count,
    COUNT(CASE WHEN result IS NOT NULL THEN 1 END) as with_result,
    COUNT(CASE WHEN result IS NULL THEN 1 END) as without_result
FROM tasks
GROUP BY status;
"

# 2. 检查任务创建时间顺序
docker exec -it async_ai_postgres psql -U postgres -d async_ai_task_runner -c "
SELECT id, status, created_at, updated_at
FROM tasks
ORDER BY created_at DESC
LIMIT 10;
"

# 3. 验证任务ID连续性
docker exec -it async_ai_postgres psql -U postgres -d async_ai_task_runner -c "
SELECT
    COUNT(*) as total_tasks,
    MIN(id) as min_id,
    MAX(id) as max_id,
    MAX(id) - MIN(id) + 1 as expected_count
FROM tasks;
"
```

### 5.2 API 与数据库一致性验证

```bash
# 1. 通过 API 获取任务数量
API_COUNT=$(curl -s -X GET "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" | jq '. | length')

# 2. 通过数据库查询任务数量
DB_COUNT=$(docker exec -it async_ai_postgres psql -U postgres -d async_ai_task_runner -t \
  -c "SELECT COUNT(*) FROM tasks;" | tr -d ' ')

echo "API 任务数量: $API_COUNT"
echo "DB 任务数量: $DB_COUNT"

# 验证一致性
if [ "$API_COUNT" -eq "$DB_COUNT" ]; then
    echo "✅ 数据一致性验证通过"
else
    echo "❌ 数据一致性验证失败"
fi
```

### 5.3 状态流转验证

```bash
# 创建任务并监控状态变化
TASK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/tasks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "数据一致性测试任务",
    "model": "deepseek-chat",
    "priority": 1
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')
INITIAL_STATUS=$(echo $TASK_RESPONSE | jq -r '.status')

echo "任务 ID: $TASK_ID"
echo "初始状态: $INITIAL_STATUS"

# 等待任务完成并验证最终状态
sleep 10

FINAL_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/tasks/$TASK_ID")
FINAL_STATUS=$(echo $FINAL_RESPONSE | jq -r '.status')
HAS_RESULT=$(echo $FINAL_RESPONSE | jq -r '.result')

echo "最终状态: $FINAL_STATUS"
echo "包含结果: $HAS_RESULT"

# 验证状态流转的合理性
if [[ "$INITIAL_STATUS" == "PENDING" && ("$FINAL_STATUS" == "COMPLETED" || "$FINAL_STATUS" == "FAILED") ]]; then
    echo "✅ 状态流转验证通过"
else
    echo "❌ 状态流转验证失败"
fi
```

### 5.4 并发数据一致性测试

```bash
# 创建并发任务，验证数据完整性
cat > concurrent_test.sh << 'EOF'
#!/bin/bash
echo "开始并发数据一致性测试..."

# 创建 20 个并发任务
PIDS=()
for i in {1..20}; do
  curl -X POST "http://localhost:8000/api/v1/tasks" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{
      \"prompt\": \"并发测试任务 $i\",
      \"model\": \"deepseek-chat\",
      \"priority\": $((i % 3 + 1))
    }" > /tmp/task_$i.json &
  PIDS+=($!)
done

# 等待所有任务创建完成
for pid in ${PIDS[@]}; do
  wait $pid
done

# 验证数据完整性
CREATED_COUNT=$(ls -1 /tmp/task_*.json | wc -l)
echo "创建的任务文件数: $CREATED_COUNT"

# 提取任务 ID 并验证
for i in {1..20}; do
  if [ -f "/tmp/task_$i.json" ]; then
    TASK_ID=$(cat /tmp/task_$i.json | jq -r '.id')
    echo "任务 $i: ID $TASK_ID"
    rm -f "/tmp/task_$i.json"
  fi
done

echo "并发数据一致性测试完成"
EOF

chmod +x concurrent_test.sh
./concurrent_test.sh
```

---

## 📊 测试结果记录表

| 测试项目 | 测试状态 | 预期结果 | 实际结果 | 备注 |
|---------|---------|---------|---------|------|
| **基础连接测试** | | | | |
| 健康检查 | ✅/❌ | HTTP 200 + JSON | | |
| OpenAPI 文档 | ✅/❌ | 可访问 | | |
| **任务创建测试** | | | | |
| 简单任务创建 | ✅/❌ | 返回任务 ID | | |
| 优先级任务 | ✅/❌ | 正确设置优先级 | | |
| 批量任务创建 | ✅/❌ | 全部创建成功 | | |
| **任务状态测试** | | | | |
| 状态轮询 | ✅/❌ | PENDING → COMPLETED | | |
| 状态查询 | ✅/❌ | 返回正确状态 | | |
| **错误处理测试** | | | | |
| 无效输入 | ✅/❌ | HTTP 422 | | |
| 不存在任务 | ✅/❌ | HTTP 404 | | |
| **性能测试** | | | | |
| 响应时间 | ✅/❌ | < 300ms | | 实测: __ ms |
| 负载测试 | ✅/❌ | 50个并发成功 | | 成功率: __% |
| **数据一致性** | | | | |
| API vs DB | ✅/❌ | 数量一致 | | API: __, DB: __ |
| 并发完整性 | ✅/❌ | 数据完整 | | 丢失: __ 个 |

---

## 🎯 测试执行建议

### 🔥 **立即执行** (高优先级)

1. **先解决 PostgreSQL 连接问题**
   ```bash
   # 修复数据库用户认证
   docker exec -it async_ai_postgres psql -U postgres
   CREATE USER taskuser WITH PASSWORD 'taskpass';
   CREATE DATABASE async_ai_task_runner OWNER taskuser;
   GRANT ALL PRIVILEGES ON DATABASE async_ai_task_runner TO taskuser;
   ```

2. **执行基础连接测试**
   - 确保所有服务正常运行
   - 验证基本 API 功能

3. **完成端到端任务流程测试**
   - 创建任务 → 监控状态 → 验证结果

### 📋 **测试执行顺序**

1. **环境准备** (5分钟)
2. **基础连接测试** (10分钟)
3. **任务流程测试** (20分钟)
4. **错误处理测试** (15分钟)
5. **性能测试** (15分钟)
6. **数据一致性测试** (10分钟)

**预计总耗时：** 约75分钟

### 💡 **测试技巧**

1. **使用脚本自动化** - 将重复性操作写成脚本
2. **并行测试** - 利用 `&` 符号并行执行测试
3. **日志记录** - 保存测试输出用于问题排查
4. **快照对比** - 在关键步骤前后记录系统状态

---

**文档版本：** 1.0
**最后更新：** 2025-11-27
**适用于：** Async AI Task Runner v0.1.0+