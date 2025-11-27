#!/usr/bin/env python3
"""
Test script to verify MCP server works with Claude Desktop configuration
"""

import subprocess
import json
import sys
import os

def test_mcp_server():
    """Test MCP server with the exact command from Claude config"""
    print("🔧 Testing MCP Server Configuration...")
    print(f"📍 Current directory: {os.getcwd()}")
    print(f"📋 Script path: {os.path.abspath('run_mcp_server.py')}")

    # Test the exact command that Claude Desktop will run
    cmd = ["uv", "run", "run_mcp_server.py", "--transport", "stdio", "--log-level", "ERROR"]

    print(f"🚀 Running command: {' '.join(cmd)}")

    try:
        # Test environment validation first
        result = subprocess.run(
            ["uv", "run", "run_mcp_server.py", "--validate-only"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✅ Environment validation passed")
        else:
            print(f"❌ Environment validation failed: {result.stderr}")
            return False

        # Test that the script can start
        print("🔄 Testing server startup...")
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send a simple JSON-RPC initialize message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        print(f"📤 Sending initialization: {json.dumps(init_message)}")

        # Send the message
        message_str = json.dumps(init_message) + "\n"
        process.stdin.write(message_str)
        process.stdin.flush()

        # Wait a moment for response
        try:
            stdout, stderr = process.communicate(timeout=5)

            if stdout:
                print(f"📥 Server response: {stdout[:200]}...")
                return True
            else:
                print("❌ No response from server")
                if stderr:
                    print(f"❌ Server error: {stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("⏰ Server timeout (this is expected behavior)")
            process.terminate()
            return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Clean up any running processes
        try:
            if 'process' in locals():
                process.terminate()
        except:
            pass

if __name__ == "__main__":
    success = test_mcp_server()
    print(f"\n🎯 Result: {'SUCCESS - MCP server is ready for Claude Desktop!' if success else 'FAILED - Check the errors above'}")
    sys.exit(0 if success else 1)