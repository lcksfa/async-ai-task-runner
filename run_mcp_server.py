#!/usr/bin/env python3
"""
MCP Server Launcher

Starts the Model Context Protocol server for Async AI Task Runner.
This script provides a command-line interface for running the MCP server.
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.mcp.config import mcp_settings, get_mcp_config
from app.mcp.server import mcp_server

# Configure logging
logging.basicConfig(
    level=getattr(logging, mcp_settings.log_level),
    format=mcp_settings.log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/mcp_server.log") if Path("logs").exists() else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


def print_startup_info():
    """Print server startup information"""
    config = get_mcp_config()

    print("🚀 异步AI任务运行器 - MCP服务器")
    print("=" * 50)
    print(f"📋 服务器名称: {config['server']['name']}")
    print(f"🔧 版本: {config['server']['version']}")
    print(f"📝 描述: {config['server']['description']}")
    print(f"🌐 传输协议: {config['connection']['transport']}")

    if config['connection']['transport'] == 'http':
        print(f"🔗 主机: {config['connection']['host']}")
        print(f"📡 端口: {config['connection']['port']}")

    print("🛠️  可用工具:")
    print("   - create_task: 创建新的AI处理任务")
    print("   - get_task_status: 查询任务状态和详情")
    print("   - list_tasks: 列出任务（支持过滤和分页）")
    print("   - get_task_result: 获取已完成任务的结果")

    print("📚 可用资源:")
    print("   - data://tasks/schema: 任务对象结构定义")
    print("   - data://tasks/statuses: 任务状态信息")
    print("   - data://models/available: 可用的AI模型")
    print("   - data://system/stats: 系统性能统计")

    print("💬 可用提示模板:")
    print("   - task_summary: 生成任务执行摘要")
    print("   - system_health: 系统健康诊断")
    print("   - task_analysis: 任务模式深度分析")
    print("   - performance_review: 性能优化建议")

    print("=" * 50)
    print()


def print_connection_info():
    """Print connection instructions for Claude Desktop"""
    config = get_mcp_config()

    print("📱 Claude Desktop 配置:")
    print("要将此MCP服务器连接到Claude Desktop，请在Claude Desktop配置中添加以下内容：")
    print()

    if config['connection']['transport'] == 'stdio':
        print("```json")
        print("{")
        print("  \"mcpServers\": {")
        print(f"    \"async-ai-task-runner\": {{")
        print(f"      \"command\": \"python\",")
        print(f"      \"args\": [\"{project_root}/run_mcp_server.py\", \"--transport\", \"stdio\"],")
        print("      \"env\": {}")
        print("    }")
        print("  }")
        print("}")
        print("```")
    elif config['connection']['transport'] == 'http':
        print("```json")
        print("{")
        print("  \"mcpServers\": {")
        print(f"    \"async-ai-task-runner\": {{")
        print(f"      \"command\": \"python\",")
        print(f"      \"args\": [\"{project_root}/run_mcp_server.py\", \"--transport\", \"http\", \"--host\", \"{config['connection']['host']}\", \"--port\", \"{config['connection']['port']}\"],")
        print("      \"env\": {}")
        print("    }")
        print("  }")
        print("}")
        print("```")

    print()
    print("📖 更多信息请参考：")
    print("   - MCP协议: https://modelcontextprotocol.io/")
    print("   - Claude Desktop集成: https://docs.anthropic.com/claude/docs/mcp")
    print()


def validate_environment(quiet=False):
    """Validate the runtime environment"""
    if not quiet:
        print("🔍 环境验证：")

    # Check required directories
    required_dirs = ["app", "app/mcp", "app/mcp/tools", "app/mcp/resources", "app/mcp/prompts"]
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            if not quiet:
                print(f"   ✅ {dir_path}")
        else:
            if not quiet:
                print(f"   ❌ {dir_path} - Missing directory")
            return False

    # Check required modules
    try:
        from app.database import get_db_session
        if not quiet:
            print("   ✅ Database module")
    except ImportError as e:
        if not quiet:
            print(f"   ❌ Database module: {e}")
        return False

    try:
        from app.crud import task as task_crud
        if not quiet:
            print("   ✅ CRUD module")
    except ImportError as e:
        if not quiet:
            print(f"   ❌ CRUD module: {e}")
        return False

    try:
        from app.schemas import TaskCreate, TaskResponse
        if not quiet:
            print("   ✅ Schemas module")
    except ImportError as e:
        if not quiet:
            print(f"   ❌ Schemas module: {e}")
        return False

    # Check MCP dependencies
    try:
        import mcp
        if not quiet:
            print("   ✅ MCP library")
    except ImportError as e:
        if not quiet:
            print(f"   ❌ MCP library: {e}")
            print("     Run: uv sync")
        return False

    # Check environment variables
    if Path(".env").exists():
        if not quiet:
            print("   ✅ .env file found")
    else:
        if not quiet:
            print("   ⚠️  .env file not found (optional)")

    if not quiet:
        print()
    return True


async def run_stdio_server():
    """Run MCP server with stdio transport"""
    # Note: No print statements in stdio mode - only JSON communication allowed
    try:
        # Use stdio transport for Claude Desktop integration
        from mcp.server.stdio import stdio_server
        from mcp.server.models import InitializationOptions
        from mcp.server.lowlevel.server import NotificationOptions

        logger.info("MCP server ready for stdio communication")
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=mcp_settings.server_name,
                    server_version=mcp_settings.server_version,
                    capabilities=mcp_server.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    ),
                ),
            )

    except KeyboardInterrupt:
        # Clean exit - no print in stdio mode
        import sys
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        # Only log error, don't print to stdout in stdio mode
        import sys
        sys.exit(1)


async def run_http_server(host: str, port: int):
    """Run MCP server with HTTP transport"""
    logger.info(f"Starting MCP server on http://{host}:{port}...")

    try:
        await mcp_server.run(host=host, port=port)

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Async AI Task Runner MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_mcp_server.py                    # Run with stdio transport (default for Claude Desktop)
  python run_mcp_server.py --transport http   # Run with HTTP transport
  python run_mcp_server.py --host 0.0.0.0    # Listen on all interfaces
  python run_mcp_server.py --port 8001        # Use custom port
  python run_mcp_server.py --validate-only     # Only validate environment
        """
    )

    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type for MCP communication (default: stdio)"
    )

    parser.add_argument(
        "--host",
        default=mcp_settings.host,
        help=f"Host to bind HTTP server to (default: {mcp_settings.host})"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=mcp_settings.port,
        help=f"Port for HTTP server (default: {mcp_settings.port})"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate environment and exit"
    )

    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print server configuration and exit"
    )

    parser.add_argument(
        "--print-connection",
        action="store_true",
        help="Print Claude Desktop connection instructions and exit"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=mcp_settings.log_level,
        help=f"Logging level (default: {mcp_settings.log_level})"
    )

    args = parser.parse_args()

    # Update logging level if specified
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Only print startup information for HTTP mode (stdio mode requires clean JSON communication)
    if args.transport != "stdio":
        print_startup_info()

    # Validate environment
    quiet_mode = args.transport == "stdio"
    if not validate_environment(quiet=quiet_mode):
        if not quiet_mode:
            print("❌ Environment validation failed")
        sys.exit(1)

    # Handle special commands
    if args.validate_only:
        print("✅ Environment validation passed")
        sys.exit(0)

    if args.print_config:
        print("⚙️  Server Configuration:")
        print(json.dumps(get_mcp_config(), indent=2))
        sys.exit(0)

    if args.print_connection:
        print_connection_info()
        sys.exit(0)

    # Only print connection info for non-stdio modes
    if args.transport != "stdio":
        print_connection_info()

    # Create logs directory if needed
    Path("logs").mkdir(exist_ok=True)

    # Start the appropriate server
    try:
        if args.transport == "stdio":
            asyncio.run(run_stdio_server())
        else:
            asyncio.run(run_http_server(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()