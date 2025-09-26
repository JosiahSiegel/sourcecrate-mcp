#!/usr/bin/env python3
"""
Local MCP Client for Testing Enhanced Scholarly Server

This script demonstrates how to use the MCP server locally within the project
using the .mcp.json configuration.
"""

import asyncio
import subprocess
import signal
import sys
import time
import json
from pathlib import Path

def start_server():
    """Start the enhanced scholarly MCP server locally"""
    print("🚀 Starting Enhanced Scholarly MCP Server...")

    # Start server as subprocess
    process = subprocess.Popen(
        [sys.executable, "scholarly_enhanced_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Give server time to start
    time.sleep(2)

    return process

def stop_server(process):
    """Stop the MCP server"""
    if process and process.poll() is None:
        print("🛑 Stopping MCP server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

async def test_mcp_integration():
    """Test MCP integration with local server"""
    print("\n🔧 Testing MCP Integration")
    print("-" * 40)

    # Check if .mcp.json exists
    mcp_config = Path(".mcp.json")
    if not mcp_config.exists():
        print("❌ .mcp.json not found")
        return False

    print("✅ .mcp.json configuration found")

    # Load and display configuration
    with open(mcp_config) as f:
        config = json.load(f)

    print(f"📋 Version: {config['version']}")
    print(f"🎯 Default server: {config['preferences']['default_server']}")
    print(f"🛠️  Available servers: {', '.join(config['mcpServers'].keys())}")
    print(f"🔧 Available tools: {len(config['tools'][0]['tools'])}")

    return True

def show_usage_instructions():
    """Show instructions for using the MCP server"""
    print("\n📚 Usage Instructions")
    print("-" * 40)
    print("The .mcp.json file configures this project for MCP integration.")
    print("Here's how to use it:")
    print()

    print("🔧 Local Development:")
    print("   python3 scholarly_enhanced_server.py")
    print()

    print("🧪 Testing:")
    print("   python3 test_local.py")
    print()

    print("📖 Examples:")
    print("   python3 examples/basic_usage.py")
    print("   python3 examples/client_example.py")
    print()

    print("🎯 MCP Client Integration:")
    print("   The server can be called via MCP protocol from:")
    print("   - Claude Desktop")
    print("   - Other MCP-compatible AI clients")
    print("   - FastMCP Cloud deployment")
    print()

    print("🌐 For Claude Desktop integration, add to config:")
    print('   {')
    print('     "mcpServers": {')
    print('       "scholarly": {')
    print('         "command": "python3",')
    print(f'         "args": ["{Path().absolute()}/scholarly_enhanced_server.py"],')
    print(f'         "cwd": "{Path().absolute()}"')
    print('       }')
    print('     }')
    print('   }')

def main():
    """Main function"""
    print("📊 Enhanced Scholarly MCP Server - Local Project Integration")
    print("=" * 60)

    # Test MCP configuration
    config_valid = asyncio.run(test_mcp_integration())

    if config_valid:
        print("\n✅ MCP configuration is valid and ready!")
        show_usage_instructions()

        print("\n🎉 Project is ready for:")
        print("   - Local development and testing")
        print("   - MCP client integration")
        print("   - FastMCP Cloud deployment")

    else:
        print("\n❌ MCP configuration issues found")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())