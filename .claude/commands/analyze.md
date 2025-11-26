# 代码分析命令

## 用途
深度代码分析、技术原理讲解和学习指导

## 命令定义

### `/analyze-architecture [component]`
分析项目架构和特定组件

**参数**:
- `component`: 可选，指定要分析的组件 (api, database, worker, mcp)

**功能**:
- 分析整体架构设计
- 解析组件间的交互关系
- 识别设计模式和最佳实践
- 生成架构图和说明文档

### `/analyze-code [file_path]`
深度分析指定文件的代码

**参数**:
- `file_path`: 可选，指定要分析的文件路径

**功能**:
- 代码质量评估
- 复杂度分析
- 潜在问题识别
- 最佳实践建议

### `/analyze-technology [tech]`
分析特定技术的使用和原理

**参数**:
- `tech`: 技术名称 (fastapi, pydantic, sqlalchemy, celery, redis, docker)

**功能**:
- 技术原理深度讲解
- 使用场景分析
- 配置和优化建议
- 相关学习资源推荐

### `/analyze-performance [endpoint]`
分析系统性能和瓶颈

**参数**:
- `endpoint`: 可选，指定要分析的API端点

**功能**:
- 性能基准测试
- 瓶颈识别和分析
- 优化建议
- 监控配置指导