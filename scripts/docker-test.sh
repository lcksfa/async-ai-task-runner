#!/bin/bash

# 🚀 Async AI Task Runner - Docker测试脚本
# 用于测试Docker容器化部署

set -e

echo "🐳 Async AI Task Runner - Docker 测试脚本"
echo "=========================================="

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

# 检查Docker是否运行
check_docker() {
    log_info "检查Docker环境..."

    if ! docker info > /dev/null 2>&1; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi

    if ! docker-compose --version > /dev/null 2>&1; then
        log_error "Docker Compose未安装"
        exit 1
    fi

    log_success "Docker环境检查通过"
}

# 清理之前的容器和镜像
cleanup() {
    log_info "清理之前的容器..."

    docker-compose down --remove-orphans 2>/dev/null || true

    # 清理悬空的镜像
    docker image prune -f > /dev/null 2>&1 || true

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

    # 首先启动数据库和Redis
    log_info "启动数据库和Redis..."
    docker-compose up -d postgres redis

    # 等待数据库和Redis就绪
    log_info "等待数据库和Redis就绪..."
    sleep 10

    # 启动应用服务
    log_info "启动Web应用和Worker..."
    docker-compose up -d web worker

    # 等待应用启动
    log_info "等待应用启动..."
    sleep 15

    # 可选启动Flower监控
    log_info "启动Flower监控..."
    docker-compose up -d flower

    log_success "所有服务启动完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."

    echo "容器状态:"
    docker-compose ps

    echo ""
    log_info "检查服务健康状态..."

    # 检查PostgreSQL
    if docker-compose exec -T postgres pg_isready -U taskuser -d task_runner > /dev/null 2>&1; then
        log_success "✅ PostgreSQL运行正常"
    else
        log_error "❌ PostgreSQL异常"
    fi

    # 检查Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "✅ Redis运行正常"
    else
        log_error "❌ Redis异常"
    fi

    # 检查Web应用
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        log_success "✅ Web应用运行正常"
    else
        log_warning "⚠️ Web应用可能还在启动中"
    fi

    # 检查Flower
    if curl -f http://localhost:5555/ > /dev/null 2>&1; then
        log_success "✅ Flower监控运行正常"
    else
        log_warning "⚠️ Flower监控可能还在启动中"
    fi
}

# 测试API
test_api() {
    log_info "测试API接口..."

    # 等待API完全启动
    sleep 10

    # 测试健康检查
    echo "1. 测试健康检查接口..."
    if curl -s http://localhost:8000/api/v1/health | python3 -m json.tool > /dev/null 2>&1; then
        log_success "✅ 健康检查接口正常"
    else
        log_warning "⚠️ 健康检查接口异常"
    fi

    # 测试创建任务
    echo "2. 测试创建任务接口..."
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"prompt": "计算1+1等于多少？", "provider": "deepseek"}' \
        http://localhost:8000/api/v1/tasks)

    if echo "$response" | python3 -c "import sys, json; json.load(sys.stdin)" > /dev/null 2>&1; then
        log_success "✅ 创建任务接口正常"
        task_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
        echo "   创建的任务ID: $task_id"
    else
        log_warning "⚠️ 创建任务接口异常"
        echo "   响应: $response"
    fi
}

# 显示日志
show_logs() {
    log_info "显示应用日志..."
    docker-compose logs --tail=20 web
}

# 显示访问信息
show_info() {
    echo ""
    log_info "🎉 部署完成！"
    echo ""
    echo "📱 访问地址:"
    echo "  - Web应用: http://localhost:8000"
    echo "  - API文档: http://localhost:8000/docs"
    echo "  - Flower监控: http://localhost:5555 (用户: admin, 密码: admin123)"
    echo ""
    echo "🔧 管理命令:"
    echo "  - 查看日志: docker-compose logs -f [service_name]"
    echo "  - 停止服务: docker-compose down"
    echo "  - 重启服务: docker-compose restart [service_name]"
    echo ""
}

# 主函数
main() {
    echo "开始Docker测试部署..."
    echo ""

    check_docker
    cleanup
    build_images
    start_services
    check_services
    test_api
    show_info

    log_success "🚀 Docker测试部署完成！"
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
    "check")
        check_services
        ;;
    "test")
        test_api
        ;;
    "logs")
        show_logs
        ;;
    "all"|*)
        main
        ;;
esac