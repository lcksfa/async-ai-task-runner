#!/bin/bash

# =============================================================================
# Async AI Task Runner 基础连接测试
# =============================================================================
# 用途: 验证所有服务的基本连接和健康状态
# 用法: ./basic-connectivity-test.sh
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_BASE="http://localhost:8000/api/v1"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔍 Async AI Task Runner 基础连接测试"
echo "========================================"

# 1. Docker 容器状态检查
log_info "1. 检查 Docker 容器状态..."

if ! docker-compose ps | grep -q "Up"; then
    log_error "Docker 容器未正常运行，请先执行: docker-compose up -d"
    exit 1
fi

containers=$(docker-compose ps --services | wc -l)
running_containers=$(docker-compose ps --filter "status=running" --services | wc -l)

if [ "$containers" -eq "$running_containers" ]; then
    log_success "所有 $containers 个容器正在运行"
else
    log_warning "部分容器未运行 ($running_containers/$containers)"
fi

# 2. FastAPI 服务健康检查
log_info "2. 检查 FastAPI 服务..."

health_response=$(curl -s "$API_BASE/health" 2>/dev/null || echo '{"error":"connection_failed"}')

if echo "$health_response" | jq -e '.status' > /dev/null 2>&1; then
    app_name=$(echo "$health_response" | jq -r '.app_name' 2>/dev/null || echo 'Unknown')
    version=$(echo "$health_response" | jq -r '.version' 2>/dev/null || echo 'Unknown')
    status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo 'Unknown')

    log_success "FastAPI 服务健康 - 状态: $status, 应用: $app_name, 版本: $version"
else
    log_error "FastAPI 服务健康检查失败"
    exit 1
fi

# 3. PostgreSQL 连接检查
log_info "3. 检查 PostgreSQL 连接..."

if docker exec async_ai_postgres psql -U taskuser -d task_runner -c "SELECT 1;" > /dev/null 2>&1; then
    db_version=$(docker exec async_ai_postgres psql -U taskuser -d task_runner -t -c "SELECT version();" 2>/dev/null | head -c 20)
    log_success "PostgreSQL 连接正常 - $db_version"
else
    log_error "PostgreSQL 连接失败"
    exit 1
fi

# 4. Redis 连接检查
log_info "4. 检查 Redis 连接..."

redis_response=$(docker exec async_ai_redis redis-cli ping 2>/dev/null || echo "FAILED")

if [ "$redis_response" = "PONG" ]; then
    redis_info=$(docker exec async_ai_redis redis-cli info server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
    log_success "Redis 连接正常 - 版本: $redis_info"
else
    log_error "Redis 连接失败 - 响应: $redis_response"
    exit 1
fi

# 5. Celery Worker 状态检查
log_info "5. 检查 Celery Worker 状态..."

worker_stats=$(docker exec async_ai_worker celery -A app.celery_app inspect stats 2>/dev/null || echo "FAILED")

if echo "$worker_stats" | grep -q "pool" 2>/dev/null; then
    log_success "Celery Worker 运行正常"
else
    log_warning "Celery Worker 状态检查失败，但可能仍在运行"
fi

# 6. Flower 监控界面检查
log_info "6. 检查 Flower 监控界面..."

flower_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5555 2>/dev/null || echo "000")

if [ "$flower_response" = "200" ]; then
    log_success "Flower 监控界面可访问"
else
    log_warning "Flower 监控界面访问异常 - HTTP: $flower_response"
fi

# 7. 数据库表结构检查
log_info "7. 检查数据库表结构..."

table_exists=$(docker exec async_ai_postgres psql -U taskuser -d task_runner -t -c "
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'tasks';
" 2>/dev/null | tr -d ' ')

if [ "$table_exists" = "1" ]; then
    log_success "数据库表结构存在"

    # 检查表中的记录数
    record_count=$(docker exec async_ai_postgres psql -U taskuser -d task_runner -t -c "SELECT COUNT(*) FROM tasks;" 2>/dev/null | tr -d ' ')
    log_info "tasks 表中当前有 $record_count 条记录"
else
    log_error "数据库表结构缺失"
    exit 1
fi

# 8. API 端点基本测试
log_info "8. 测试主要 API 端点..."

# 测试任务列表接口
tasks_response=$(curl -s "$API_BASE/tasks" 2>/dev/null || echo '{"error":"failed"}')

if echo "$tasks_response" | jq -e '. | type == "array"' > /dev/null 2>&1; then
    task_count=$(echo "$tasks_response" | jq '. | length' 2>/dev/null || echo "0")
    log_success "任务列表接口正常 - 当前任务数: $task_count"
else
    log_error "任务列表接口异常"
    exit 1
fi

# 测试 OpenAPI 文档
docs_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")

if [ "$docs_response" = "200" ]; then
    log_success "OpenAPI 文档可访问"
else
    log_warning "OpenAPI 文档访问异常 - HTTP: $docs_response"
fi

echo "========================================"
log_success "🎉 基础连接测试完成！"
log_info "所有核心服务运行正常，可以开始集成测试"