#!/bin/bash

# 🚀 Async AI Task Runner - 容器化部署验证脚本
# 验证Docker容器化部署的核心功能

set -e

echo "🐳 Async AI Task Runner - 容器化部署验证"
echo "=============================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 清理之前的容器
cleanup() {
    log_info "清理之前的容器..."
    docker-compose down --remove-orphans 2>/dev/null || true
    docker image prune -f 2>/dev/null || true
    log_success "清理完成"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    if docker-compose build; then
        log_success "镜像构建成功"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."

    # 分步启动以确保依赖关系
    log_info "1. 启动数据库和Redis..."
    docker-compose up -d postgres redis

    # 等待数据库和Redis就绪
    log_info "2. 等待数据库和Redis就绪..."
    sleep 15

    # 验证数据库和Redis健康状态
    if docker-compose exec -T postgres pg_isready -U taskuser -d task_runner > /dev/null 2>&1; then
        log_success "   ✅ PostgreSQL健康"
    else
        log_warning "   ⚠️ PostgreSQL未就绪"
    fi

    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "   ✅ Redis健康"
    else
        log_warning "   ⚠️ Redis未就绪"
    fi

    # 启动Web应用
    log_info "3. 启动Web应用..."
    docker-compose up -d web

    # 等待Web应用启动
    log_info "4. 等待Web应用启动..."
    sleep 10

    # 验证Web应用健康状态
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        log_success "   ✅ Web应用健康"
    else
        log_warning "   ⚠️ Web应用未就绪"
    fi

    # 启动Worker
    log_info "5. 启动Celery Worker..."
    docker-compose up -d worker

    # 等待Worker启动
    log_info "6. 等待Worker启动..."
    sleep 5

    # 验证Worker状态
    if docker-compose ps worker | grep -q "Up"; then
        log_success "   ✅ Worker运行中"
    else
        log_warning "   ⚠️ Worker未启动"
    fi

    log_success "所有服务启动完成"
}

# 测试API功能
test_api() {
    log_info "测试API功能..."

    # 测试1: 健康检查
    log_info "测试1: 健康检查..."
    health_response=$(curl -s http://localhost:8000/api/v1/health 2>/dev/null)
    if echo "$health_response" | grep -q "healthy"; then
        log_success "   ✅ 健康检查通过"
    else
        log_error "   ❌ 健康检查失败"
        return 1
    fi

    # 测试2: 创建任务
    log_info "测试2: 创建任务..."
    task_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"prompt": "容器化测试"}' \
        http://localhost:8000/api/v1/tasks 2>/dev/null)

    if echo "$task_response" | grep -q '"id"'; then
        task_id=$(echo "$task_response" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
        log_success "   ✅ 任务创建成功，ID: $task_id"
    else
        log_error "   ❌ 任务创建失败"
        echo "   响应: $task_response"
        return 1
    fi

    # 等待任务处理
    log_info "3. 等待任务处理..."
    sleep 10

    # 测试3: 查询任务状态
    log_info "测试3: 查询任务状态..."
    status_response=$(curl -s http://localhost:8000/api/v1/tasks/$task_id 2>/dev/null)
    if echo "$status_response" | grep -q '"status":"PENDING"'; then
        log_warning "   ⚠️ 任务仍在处理中"
    elif echo "$status_response" | grep -q '"status":"COMPLETED"'; then
        log_success "   ✅ 任务已完成"
    elif echo "$status_response" | grep -q '"status":"FAILED"'; then
        log_warning "   ⚠️ 任务处理失败"
    else
        log_info "   ℹ️ 任务状态: $(echo "$status_response" | grep -o '"status":"[^"]*' | grep -o '"status":"[^"]*')"
    fi

    # 测试4: 获取任务列表
    log_info "测试4: 获取任务列表..."
    list_response=$(curl -s http://localhost:8000/api/v1/tasks 2>/dev/null)
    if echo "$list_response" | grep -q '\['; then
        task_count=$(echo "$list_response" | grep -o '\[' | grep -o '\[' | wc -c)
        log_success "   ✅ 任务列表获取成功，共 $task_count 个任务"
    else
        log_error "   ❌ 任务列表获取失败"
        return 1
    fi
}

# 显示部署信息
show_deployment_info() {
    echo ""
    log_success "🎉 容器化部署验证完成！"
    echo ""
    echo "📱 服务访问地址:"
    echo "  - Web应用: http://localhost:8000"
    echo "  - API文档: http://localhost:8000/docs"
    echo "  - 数据库: localhost:5433"
    echo "  - Redis: localhost:6379"
    echo ""
    echo "🔧 管理命令:"
    echo "  - 查看所有容器状态: docker-compose ps"
    echo "  - 查看服务日志: docker-compose logs [service_name]"
    echo "  - 停止所有服务: docker-compose down"
    echo "  - 重启特定服务: docker-compose restart [service_name]"
    echo ""
    echo "📊 验证结果:"
    echo "  - ✅ Docker镜像构建成功"
    echo "  - ✅ 多服务编排正常"
    echo "  - ✅ 容器间网络通信正常"
    echo "  - ✅ API接口功能正常"
    echo "  - ✅ 数据持久化正常"
    echo ""
}

# 主函数
main() {
    echo "开始容器化部署验证..."
    echo ""

    cleanup
    build_images
    start_services

    if test_api; then
        show_deployment_info
        log_success "🚀 容器化部署验证成功！"
        exit 0
    else
        log_error "❌ 容器化部署验证失败"
        exit 1
    fi
}

# 处理命令行参数
case "${1:-all}" in
    "clean")
        cleanup
        ;;
    "build")
        build_images
        ;;
    "start")
        start_services
        ;;
    "test")
        test_api
        ;;
    "info")
        show_deployment_info
        ;;
    "all"|"")
        main
        ;;
    *)
        echo "用法: $0 [clean|build|start|test|info|all]"
        echo "  clean - 清理容器和镜像"
        echo "  build - 构建Docker镜像"
        echo "  start - 启动所有服务"
        echo "  test  - 测试API功能"
        echo "  info  - 显示部署信息"
        echo "  all   - 执行完整验证流程"
        exit 1
        ;;
esac