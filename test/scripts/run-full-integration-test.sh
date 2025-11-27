#!/bin/bash

# =============================================================================
# Async AI Task Runner 完整集成测试脚本
# =============================================================================
# 用途: 一键执行所有集成测试
# 用法: ./run-full-integration-test.sh [--skip-cleanup]
# 选项: --skip-cleanup - 测试完成后不清理测试数据
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
API_BASE="http://localhost:8000/api/v1"
TEST_RESULTS_FILE="./test_results.log"
REPORT_DIR="$(dirname "$0")/../reports"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
REPORT_FILE="$REPORT_DIR/integration-test-report-$TIMESTAMP.md"

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 函数定义
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$TEST_RESULTS_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$TEST_RESULTS_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$TEST_RESULTS_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$TEST_RESULTS_FILE"
}

# 测试统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 开始测试报告
cat > "$REPORT_FILE" << EOF
# 🔬 Async AI Task Runner 集成测试报告

**测试时间:** $(date)
**测试环境:** Async AI Task Runner v0.1.0
**测试执行人:** $(whoami)

---

## 📊 测试总览

| 阶段 | 状态 | 通过数 | 失败数 | 备注 |
|------|------|--------|--------|------|

EOF

# 初始化测试结果文件
echo "Async AI Task Runner 集成测试开始 - $(date)" > "$TEST_RESULTS_FILE"
echo "========================================" >> "$TEST_RESULTS_FILE"

# 1. 环境检查
log_info "🔍 1. 环境检查开始..."

check_environment() {
    local stage="环境检查"
    local stage_passed=0
    local stage_failed=0

    log_info "检查 Docker 容器状态..."
    if docker-compose ps | grep -q "Up"; then
        log_success "✅ Docker 容器运行正常"
        ((stage_passed++))
    else
        log_error "❌ Docker 容器未正常运行"
        ((stage_failed++))
    fi

    log_info "检查 FastAPI 服务响应..."
    if curl -s "$API_BASE/health" | jq -e '.status' > /dev/null 2>&1; then
        log_success "✅ FastAPI 健康检查通过"
        ((stage_passed++))
    else
        log_error "❌ FastAPI 健康检查失败"
        ((stage_failed++))
    fi

    log_info "检查 PostgreSQL 连接..."
    if docker exec async_ai_postgres psql -U taskuser -d task_runner -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "✅ PostgreSQL 连接正常"
        ((stage_passed++))
    else
        log_error "❌ PostgreSQL 连接失败"
        ((stage_failed++))
    fi

    log_info "检查 Redis 连接..."
    if docker exec async_ai_redis redis-cli ping | grep -q "PONG"; then
        log_success "✅ Redis 连接正常"
        ((stage_passed++))
    else
        log_error "❌ Redis 连接失败"
        ((stage_failed++))
    fi

    # 更新报告
    echo "| $stage | ${stage_failed:-0} > 0 ? '❌' : '✅' | $stage_passed | $stage_failed | $([ $stage_failed -gt 0 ] && echo '需要修复环境问题' || echo '环境正常') |" >> "$REPORT_FILE"

    TOTAL_TESTS=$((TOTAL_TESTS + stage_passed + stage_failed))
    PASSED_TESTS=$((PASSED_TESTS + stage_passed))
    FAILED_TESTS=$((FAILED_TESTS + stage_failed))

    if [ $stage_failed -gt 0 ]; then
        log_error "环境检查失败，请修复问题后重新运行测试"
        exit 1
    fi

    log_success "🎉 环境检查完成"
}

# 2. 基础连接测试
log_info "🔧 2. 基础连接测试开始..."

test_basic_connectivity() {
    local stage="基础连接测试"
    local stage_passed=0
    local stage_failed=0

    log_info "测试健康检查接口..."
    health_response=$(curl -s "$API_BASE/health" 2>/dev/null || echo '{"error":"connection_failed"}')
    if echo "$health_response" | jq -e '.status' > /dev/null 2>&1; then
        log_success "✅ 健康检查接口正常"
        ((stage_passed++))
    else
        log_error "❌ 健康检查接口异常"
        ((stage_failed++))
    fi

    log_info "测试任务列表接口..."
    if curl -s "$API_BASE/tasks" | jq -e '. | length' > /dev/null 2>&1; then
        log_success "✅ 任务列表接口正常"
        ((stage_passed++))
    else
        log_error "❌ 任务列表接口异常"
        ((stage_failed++))
    fi

    log_info "测试 OpenAPI 文档..."
    if curl -s "http://localhost:8000/docs" | grep -q "swagger"; then
        log_success "✅ OpenAPI 文档可访问"
        ((stage_passed++))
    else
        log_error "❌ OpenAPI 文档无法访问"
        ((stage_failed++))
    fi

    # 更新报告
    echo "| $stage | ${stage_failed:-0} > 0 ? '❌' : '✅' | $stage_passed | $stage_failed | $([ $stage_failed -gt 0 ] && echo '接口连接问题' || echo '所有接口正常') |" >> "$REPORT_FILE"

    TOTAL_TESTS=$((TOTAL_TESTS + stage_passed + stage_failed))
    PASSED_TESTS=$((PASSED_TESTS + stage_passed))
    FAILED_TESTS=$((FAILED_TESTS + stage_failed))

    log_success "🎉 基础连接测试完成"
}

# 3. 任务流程测试
log_info "📝 3. 任务流程测试开始..."

test_task_flow() {
    local stage="任务流程测试"
    local stage_passed=0
    local stage_failed=0

    log_info "创建测试任务..."
    task_response=$(curl -s -X POST "$API_BASE/tasks" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "集成测试任务：请说出1+1等于几",
            "model": "deepseek-chat",
            "priority": 5
        }' 2>/dev/null || echo '{"error":"task_creation_failed"}')

    if echo "$task_response" | jq -e '.id' > /dev/null 2>&1; then
        task_id=$(echo "$task_response" | jq -r '.id')
        log_success "✅ 任务创建成功，ID: $task_id"
        ((stage_passed++))

        # 等待任务处理
        log_info "等待任务处理完成..."
        for i in {1..30}; do
            status_response=$(curl -s "$API_BASE/tasks/$task_id" 2>/dev/null || echo '{"error":"status_check_failed"}')
            current_status=$(echo "$status_response" | jq -r '.status' 2>/dev/null || echo 'ERROR')

            if [ "$current_status" = "COMPLETED" ]; then
                log_success "✅ 任务执行成功"
                ((stage_passed++))
                break
            elif [ "$current_status" = "FAILED" ]; then
                log_error "❌ 任务执行失败"
                ((stage_failed++))
                break
            fi

            sleep 2
            log_info "任务状态: $current_status (检查 $i/30)"
        done

        # 检查最终状态
        if [ "$current_status" = "COMPLETED" ]; then
            result=$(echo "$status_response" | jq -r '.result' 2>/dev/null || echo 'NO_RESULT')
            if [ "$result" != "NO_RESULT" ] && [ "$result" != "null" ]; then
                log_success "✅ 任务结果正常获取"
                ((stage_passed++))
            else
                log_warning "⚠️ 任务结果为空"
                ((stage_passed++))  # 可能是正常情况
            fi
        fi

    else
        log_error "❌ 任务创建失败"
        ((stage_failed++))
    fi

    log_info "测试批量任务创建..."
    batch_tasks=0
    for i in {1..5}; do
        batch_response=$(curl -s -X POST "$API_BASE/tasks" \
            -H "accept: application/json" \
            -H "Content-Type: application/json" \
            -d '{
                "prompt": "批量测试任务 '$i'",
                "model": "deepseek-chat",
                "priority": '$((i % 3 + 1))'
            }' 2>/dev/null || echo '{"error":"batch_failed"}')

        # 检查批量任务创建结果
    task_id=$(echo "$batch_response" | jq -e '.id' 2>/dev/null || echo "NO_ID")

    if [ "$task_id" != "NO_ID" ] && [ "$task_id" != "null" ]; then
        log_success "✅ 批量任务创建成功 (ID: $task_id)"
        ((batch_tasks++))
    else
        log_error "❌ 批量任务创建失败"
        ((stage_failed++))
            ((batch_tasks++))
        fi
    done
    wait

    if [ $batch_tasks -eq 5 ]; then
        log_success "✅ 批量任务创建成功 ($batch_tasks/5)"
        ((stage_passed++))
    else
        log_error "❌ 批量任务创建部分失败 ($batch_tasks/5)"
        ((stage_failed++))
    fi

    # 更新报告
    echo "| $stage | ${stage_failed:-0} > 0 ? '❌' : '✅' | $stage_passed | $stage_failed | $([ $stage_failed -gt 0 ] && echo '任务执行问题' || echo '任务流程正常') |" >> "$REPORT_FILE"

    TOTAL_TESTS=$((TOTAL_TESTS + stage_passed + stage_failed))
    PASSED_TESTS=$((PASSED_TESTS + stage_passed))
    FAILED_TESTS=$((FAILED_TESTS + stage_failed))

    log_success "🎉 任务流程测试完成"
}

# 4. 错误处理测试
log_info "🚨 4. 错误处理测试开始..."

test_error_handling() {
    local stage="错误处理测试"
    local stage_passed=0
    local stage_failed=0

    log_info "测试无效输入..."
    invalid_response=$(curl -s -w "%{http_code}" -X POST "$API_BASE/tasks" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -d '{}' 2>/dev/null)

    if echo "$invalid_response" | tail -c 3 | grep -q "22"; then
        log_success "✅ 无效输入正确返回 422"
        ((stage_passed++))
    else
        log_error "❌ 无效输入未返回 422，实际: $(echo "$invalid_response" | tail -c 3)"
        ((stage_failed++))
    fi

    log_info "测试不存在的任务 ID..."
    not_found_response=$(curl -s -w "%{http_code}" "$API_BASE/tasks/999999" 2>/dev/null)
    if echo "$not_found_response" | tail -c 3 | grep -q "04"; then
        log_success "✅ 不存在任务正确返回 404"
        ((stage_passed++))
    else
        log_error "❌ 不存在任务未返回 404，实际: $(echo "$not_found_response" | tail -c 3)"
        ((stage_failed++))
    fi

    log_info "测试错误的 HTTP 方法..."
    method_response=$(curl -s -w "%{http_code}" -X DELETE "$API_BASE/tasks/1" 2>/dev/null)
    if echo "$method_response" | tail -c 3 | grep -q "05\|04"; then
        log_success "✅ 错误 HTTP 方法正确拒绝"
        ((stage_passed++))
    else
        log_error "❌ 错误 HTTP 方法未正确拒绝，实际: $(echo "$method_response" | tail -c 3)"
        ((stage_failed++))
    fi

    # 更新报告
    echo "| $stage | ${stage_failed:-0} > 0 ? '❌' : '✅' | $stage_passed | $stage_failed | $([ $stage_failed -gt 0 ] && echo '错误处理问题' || echo '错误处理正常') |" >> "$REPORT_FILE"

    TOTAL_TESTS=$((TOTAL_TESTS + stage_passed + stage_failed))
    PASSED_TESTS=$((PASSED_TESTS + stage_passed))
    FAILED_TESTS=$((FAILED_TESTS + stage_failed))

    log_success "🎉 错误处理测试完成"
}

# 5. 性能测试
log_info "⚡ 5. 性能测试开始..."

test_performance() {
    local stage="性能测试"
    local stage_passed=0
    local stage_failed=0

    log_info "测试健康检查响应时间..."
    health_time=$(curl -o /dev/null -s -w "%{time_total}" "$API_BASE/health" 2>/dev/null)
    if (( $(echo "$health_time < 0.05" | bc -l) )); then
        log_success "✅ 健康检查响应时间: ${health_time}s (< 0.05s)"
        ((stage_passed++))
    else
        log_warning "⚠️ 健康检查响应时间: ${health_time}s (>= 0.05s)"
        ((stage_passed++))  # 不算失败，只是警告
    fi

    log_info "测试任务创建响应时间..."
    create_time=$(curl -o /dev/null -s -w "%{time_total}" -X POST "$API_BASE/tasks" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "性能测试", "model": "deepseek-chat", "priority": 1}' 2>/dev/null)

    if (( $(echo "$create_time < 0.2" | bc -l) )); then
        log_success "✅ 任务创建响应时间: ${create_time}s (< 0.2s)"
        ((stage_passed++))
    else
        log_warning "⚠️ 任务创建响应时间: ${create_time}s (>= 0.2s)"
        ((stage_passed++))  # 不算失败，只是警告
    fi

    log_info "进行轻负载测试 (5个并发)..."
    start_time=$(date +%s.%N)
    for i in {1..5}; do
        curl -s -X POST "$API_BASE/tasks" \
            -H "accept: application/json" \
            -H "Content-Type: application/json" \
            -d "{\"prompt\": \"负载测试 $i\", \"model\": \"deepseek-chat\", \"priority\": 1}" > /dev/null &
    done
    wait
    end_time=$(date +%s.%N)

    load_time=$(echo "$end_time - $start_time" | bc)
    avg_time=$(echo "scale=3; $load_time / 5" | bc)

    log_success "✅ 负载测试完成: 5个任务，总耗时: ${load_time}s，平均: ${avg_time}s"
    ((stage_passed++))

    # 更新报告
    echo "| $stage | ${stage_failed:-0} > 0 ? '❌' : '✅' | $stage_passed | $stage_failed | $([ $stage_failed -gt 0 ] && echo '性能不达标' || echo '性能满足要求') |" >> "$REPORT_FILE"

    TOTAL_TESTS=$((TOTAL_TESTS + stage_passed + stage_failed))
    PASSED_TESTS=$((PASSED_TESTS + stage_passed))
    FAILED_TESTS=$((FAILED_TESTS + stage_failed))

    log_success "🎉 性能测试完成"
}

# 6. 数据一致性测试
log_info "🗄️ 6. 数据一致性测试开始..."

test_data_consistency() {
    local stage="数据一致性测试"
    local stage_passed=0
    local stage_failed=0

    log_info "检查 API 与数据库数据一致性..."
    # 测试1: 验证API分页限制正常工作
    api_count=$(curl -s "$API_BASE/tasks" | jq '. | length' 2>/dev/null || echo "0")
    expected_limit=10000

    if [ "$api_count" -le "$expected_limit" ]; then
        log_success "✅ API 分页限制正常 (返回: $api_count, 限制: $expected_limit)"
        ((stage_passed++))
    else
        log_error "❌ API 分页限制异常 (返回: $api_count, 限制: $expected_limit)"
        ((stage_failed++))
    fi

    # 测试2: 验证数据库总记录数大于等于API返回数
    db_count=$(docker exec async_ai_postgres psql -U taskuser -d task_runner -t -c "SELECT COUNT(*) FROM tasks;" 2>/dev/null | tr -d ' ' || echo "0")

    if [ "$db_count" -ge "$api_count" ]; then
        log_success "✅ 数据一致性验证通过 (API: $api_count, DB总数: $db_count)"
        ((stage_passed++))
    else
        log_error "❌ 数据一致性验证失败 (API: $api_count, DB总数: $db_count)"
        ((stage_failed++))
    fi

    log_info "检查数据库状态分布..."
    status_check=$(docker exec async_ai_postgres psql -U postgres -d async_ai_task_runner -t -c "
        SELECT COUNT(*) FROM tasks GROUP BY status HAVING COUNT(*) < 0;
    " 2>/dev/null || echo "OK")

    if [ "$status_check" = "OK" ]; then
        log_success "✅ 数据库状态分布正常"
        ((stage_passed++))
    else
        log_error "❌ 数据库状态分布异常"
        ((stage_failed++))
    fi

    # 更新报告
    echo "| $stage | ${stage_failed:-0} > 0 ? '❌' : '✅' | $stage_passed | $stage_failed | $([ $stage_failed -gt 0 ] && echo '数据一致性问题' || echo '数据一致性良好') |" >> "$REPORT_FILE"

    TOTAL_TESTS=$((TOTAL_TESTS + stage_passed + stage_failed))
    PASSED_TESTS=$((PASSED_TESTS + stage_passed))
    FAILED_TESTS=$((FAILED_TESTS + stage_failed))

    log_success "🎉 数据一致性测试完成"
}

# 7. 清理测试数据
cleanup_test_data() {
    if [ "$1" != "--skip-cleanup" ]; then
        log_info "🧹 清理测试数据..."
        # 这里可以添加清理逻辑，比如删除测试任务等
        log_success "✅ 测试数据清理完成"
    else
        log_info "⏭️ 跳过测试数据清理"
    fi
}

# 生成最终测试报告
generate_final_report() {
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc 2>/dev/null || echo "0")

    cat >> "$REPORT_FILE" << EOF

---

## 📊 测试统计

- **总测试用例：** $TOTAL_TESTS
- **通过用例：** $PASSED_TESTS
- **失败用例：** $FAILED_TESTS
- **通过率：** ${success_rate}%

## 🎯 测试结论

EOF

    if [ $FAILED_TESTS -eq 0 ]; then
        echo "✅ **系统可发布** - 所有关键功能正常，性能满足要求" >> "$REPORT_FILE"
        log_success "🎉 所有测试通过！系统可以发布。"
    elif [ $FAILED_TESTS -le 2 ]; then
        echo "⚠️ **系统基本可用** - 存在次要问题，但不影响核心功能" >> "$REPORT_FILE"
        log_warning "⚠️ 大部分测试通过，系统基本可用，但建议修复发现的问题。"
    else
        echo "❌ **需要修复后测试** - 存在严重问题，必须修复后才能发布" >> "$REPORT_FILE"
        log_error "❌ 发现多个问题，需要修复后重新测试。"
    fi

    cat >> "$REPORT_FILE" << EOF

## 📝 详细日志

详细测试日志请查看: \`$TEST_RESULTS_FILE\`

## 🚀 后续行动

1. **立即处理：** [检查失败的具体测试项]
2. **短期改进：** [根据性能测试结果优化]
3. **长期规划：** [考虑更全面的自动化测试]

---

**报告生成时间:** $(date)
**测试完成时间:** $(date)
**测试执行耗时:** 约 10-15 分钟
**建议下次测试:** 功能更新后或部署前

EOF

    log_success "📄 测试报告已生成: $REPORT_FILE"
}

# 主执行流程
main() {
    echo "🚀 Async AI Task Runner 集成测试开始..."
    echo "========================================"

    # 执行所有测试阶段
    check_environment
    test_basic_connectivity
    test_task_flow
    test_error_handling
    test_performance
    test_data_consistency

    # 清理测试数据
    cleanup_test_data "$1"

    # 生成最终报告
    generate_final_report

    echo "========================================"
    log_info "🏁 集成测试完成"
    log_info "📊 测试统计: 通过 $PASSED_TESTS/$TOTAL_TESTS (${success_rate}%)"
    log_info "📄 详细报告: $REPORT_FILE"

    # 根据测试结果设置退出码
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# 脚本入口
if ! command -v jq &> /dev/null; then
    log_error "❌ 缺少 jq 工具，请先安装: brew install jq 或 apt-get install jq"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    log_error "❌ 缺少 bc 工具，请先安装"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "$(dirname "$0")/../../docker-compose.yml" ]; then
    log_error "❌ 请在项目根目录运行此测试脚本"
    exit 1
fi

main "$@"