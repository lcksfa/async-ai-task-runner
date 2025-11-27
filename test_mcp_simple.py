#!/usr/bin/env python3
"""
Simple test script for MCP server functionality
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_mcp_server():
    """Test MCP server with basic protocol messages"""
    try:
        # Import the server
        from app.mcp.server import mcp_server
        from app.mcp.config import mcp_settings
        from mcp.server.models import InitializationOptions
        from mcp.server.lowlevel.server import NotificationOptions

        print("Testing MCP server initialization...")

        # Test initialization options
        init_options = InitializationOptions(
            server_name=mcp_settings.server_name,
            server_version=mcp_settings.server_version,
            capabilities=mcp_server.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            ),
        )

        print(f"✅ Server name: {mcp_settings.server_name}")
        print(f"✅ Server version: {mcp_settings.server_version}")
        print(f"✅ Capabilities: {init_options.capabilities}")

        # Test that the server object has the expected attributes
        print(f"✅ Server has list_tools method: {hasattr(mcp_server.server, 'list_tools')}")
        print(f"✅ Server has call_tool method: {hasattr(mcp_server.server, 'call_tool')}")
        print(f"✅ Server has list_resources method: {hasattr(mcp_server.server, 'list_resources')}")
        print(f"✅ Server has list_prompts method: {hasattr(mcp_server.server, 'list_prompts')}")

        print("\n🎉 MCP server test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_mcp_server()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())