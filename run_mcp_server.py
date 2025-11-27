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

    print("🚀 Async AI Task Runner - MCP Server")
    print("=" * 50)
    print(f"📋 Server Name: {config['server']['name']}")
    print(f"🔧 Version: {config['server']['version']}")
    print(f"📝 Description: {config['server']['description']}")
    print(f"🌐 Transport: {config['connection']['transport']}")

    if config['connection']['transport'] == 'http':
        print(f"🔗 Host: {config['connection']['host']}")
        print(f"📡 Port: {config['connection']['port']}")

    print("🛠️  Available Tools:")
    print("   - create_task: Create new AI processing tasks")
    print("   - get_task_status: Check task status and details")
    print("   - list_tasks: List tasks with filtering")
    print("   - get_task_result: Get results of completed tasks")

    print("📚 Available Resources:")
    print("   - data://tasks/schema: Task object schema")
    print("   - data://tasks/statuses: Task status information")
    print("   - data://models/available: Available AI models")
    print("   - data://system/stats: System performance statistics")

    print("💬 Available Prompts:")
    print("   - task_summary: Generate task execution summary")
    print("   - system_health: System health and diagnostics")
    print("   - task_analysis: Deep analysis of task patterns")
    print("   - performance_review: Performance optimization insights")

    print("=" * 50)
    print()


def print_connection_info():
    """Print connection instructions for Claude Desktop"""
    config = get_mcp_config()

    print("📱 Claude Desktop Configuration:")
    print("To connect this MCP server to Claude Desktop, add the following to your Claude Desktop config:")
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
    print("📖 For more information, see:")
    print("   - MCP Protocol: https://modelcontextprotocol.io/")
    print("   - Claude Desktop Integration: https://docs.anthropic.com/claude/docs/mcp")
    print()


def validate_environment():
    """Validate the runtime environment"""
    print("🔍 Environment Validation:")

    # Check required directories
    required_dirs = ["app", "app/mcp", "app/mcp/tools", "app/mcp/resources", "app/mcp/prompts"]
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} - Missing directory")
            return False

    # Check required modules
    try:
        from app.database import get_db_session
        print("   ✅ Database module")
    except ImportError as e:
        print(f"   ❌ Database module: {e}")
        return False

    try:
        from app.crud import task as task_crud
        print("   ✅ CRUD module")
    except ImportError as e:
        print(f"   ❌ CRUD module: {e}")
        return False

    try:
        from app.schemas import TaskCreate, TaskResponse
        print("   ✅ Schemas module")
    except ImportError as e:
        print(f"   ❌ Schemas module: {e}")
        return False

    # Check MCP dependencies
    try:
        import mcp
        print("   ✅ MCP library")
    except ImportError as e:
        print(f"   ❌ MCP library: {e}")
        print("     Run: uv sync")
        return False

    # Check environment variables
    if Path(".env").exists():
        print("   ✅ .env file found")
    else:
        print("   ⚠️  .env file not found (optional)")

    print()
    return True


async def run_stdio_server():
    """Run MCP server with stdio transport"""
    print("🔄 Starting MCP server with stdio transport...")

    try:
        # Use stdio transport for Claude Desktop integration
        import sys
        from mcp.server.stdio import stdio_server

        async def handle_client(stdin, stdout):
            await mcp_server.server.run(
                stdin,
                stdout,
                mcp_server.server.InitializationOptions(
                    server_name=mcp_settings.server_name,
                    server_version=mcp_settings.server_version,
                    capabilities=mcp_server.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

        logger.info("MCP server ready for stdio communication")
        await stdio_server(handle_client)

    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"❌ Server error: {e}")
        sys.exit(1)


async def run_http_server(host: str, port: int):
    """Run MCP server with HTTP transport"""
    print(f"🌐 Starting MCP server on http://{host}:{port}...")

    try:
        await mcp_server.run(host=host, port=port)

    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        print(f"❌ Server error: {e}")
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

    # Print startup information
    print_startup_info()

    # Validate environment
    if not validate_environment():
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

    # Print connection info by default
    if args.transport == "stdio":
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
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        print(f"❌ Startup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()