#!/usr/bin/env python3
"""
Automated Claude Code MCP Setup Script

This script helps set up the Enhanced Scholarly MCP Server for use with Claude Code.
"""

import json
import os
import sys
import platform
from pathlib import Path

def get_claude_code_config_path():
    """Get the path to Claude Code's MCP configuration directory"""
    system = platform.system()

    if system == "Windows":
        config_dir = Path(os.getenv('APPDATA', '')) / 'claude-code'
    elif system == "Darwin":  # macOS
        config_dir = Path.home() / 'Library' / 'Application Support' / 'claude-code'
    else:  # Linux and others
        config_dir = Path.home() / '.config' / 'claude-code'

    return config_dir

def get_current_directory():
    """Get the current project directory"""
    return Path(__file__).parent.absolute()

def create_mcp_config():
    """Create MCP server configuration for Claude Code"""
    project_dir = get_current_directory()

    # MCP server configuration
    config = {
        "scholarly-enhanced": {
            "command": "python3",
            "args": ["scholarly_enhanced_server.py"],
            "cwd": str(project_dir),
            "env": {
                "UNPAYWALL_EMAIL": "research@example.com",
                "MAX_PDF_SIZE_MB": "50",
                "PDF_TIMEOUT": "60",
                "PROXY_TYPE": "none",
                "RATE_LIMIT_DELAY": "1.0"
            }
        }
    }

    return config

def setup_claude_code_mcp():
    """Set up MCP server configuration for Claude Code"""
    print("🔧 Setting up Enhanced Scholarly MCP Server for Claude Code")
    print("=" * 60)

    # Get paths
    config_dir = get_claude_code_config_path()
    project_dir = get_current_directory()
    config_file = config_dir / "mcp_servers.json"

    print(f"📁 Project directory: {project_dir}")
    print(f"🔧 Claude Code config directory: {config_dir}")
    print(f"📄 MCP config file: {config_file}")

    # Create configuration
    new_config = create_mcp_config()

    # Check if config directory exists
    if not config_dir.exists():
        print(f"\n📁 Creating Claude Code config directory: {config_dir}")
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            print("✅ Directory created successfully")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            return False

    # Load existing configuration if it exists
    existing_config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
            print(f"📖 Loaded existing configuration with {len(existing_config)} server(s)")
        except Exception as e:
            print(f"⚠️  Could not read existing config: {e}")
            print("🔄 Creating new configuration file")

    # Merge configurations
    existing_config.update(new_config)

    # Write configuration
    try:
        with open(config_file, 'w') as f:
            json.dump(existing_config, f, indent=2)
        print(f"✅ MCP configuration written to: {config_file}")
        print(f"🎯 Added server: scholarly-enhanced")
    except Exception as e:
        print(f"❌ Failed to write configuration: {e}")
        return False

    return True

def verify_dependencies():
    """Verify that required dependencies are installed"""
    print("\n🔍 Verifying dependencies...")

    required_modules = [
        'fastmcp',
        'scholarly',
        'httpx',
        'aiohttp',
        'requests',
        'fitz',  # PyMuPDF
        'lxml'
    ]

    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            missing.append(module)
            print(f"  ❌ {module}")

    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("📦 Install with: pip install -r requirements_enhanced.txt")
        return False

    print("✅ All dependencies are installed")
    return True

def test_server():
    """Test that the server can be imported and run"""
    print("\n🧪 Testing server import...")

    try:
        # Test import
        sys.path.insert(0, str(get_current_directory()))
        import scholarly_enhanced_server
        print("✅ Server imports successfully")

        # Test tool registration
        tools = scholarly_enhanced_server.mcp.list_tools()
        if hasattr(tools, 'tools'):
            print(f"✅ {len(tools.tools)} tools registered")
        else:
            print("✅ Tools registered (count unknown)")

        return True
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def print_usage_instructions():
    """Print instructions for using the MCP server"""
    print("\n📚 Usage Instructions")
    print("-" * 40)
    print("After setup, restart Claude Code and try these commands:")
    print()
    print("🔍 Check MCP servers:")
    print("   /mcp list")
    print()
    print("🧪 Test the server:")
    print('   /mcp call scholarly-enhanced search_author \'{"name": "Geoffrey Hinton", "limit": 1}\'')
    print()
    print("📄 Search for papers:")
    print('   /mcp call scholarly-enhanced search_publications \'{"query": "machine learning", "limit": 3}\'')
    print()
    print("📖 Get full text (for open access papers):")
    print('   /mcp call scholarly-enhanced get_full_text_by_title \'{"title": "Attention Is All You Need", "extract_text": true}\'')
    print()
    print("💬 Natural language usage:")
    print("   Just ask Claude to search for papers, authors, or get full text!")
    print("   Example: 'Search for recent papers about transformer neural networks'")

def main():
    """Main setup function"""
    print("🚀 Enhanced Scholarly MCP Server - Claude Code Setup")
    print("=" * 60)

    # Check dependencies
    if not verify_dependencies():
        print("\n❌ Setup aborted due to missing dependencies")
        print("📦 Please run: pip install -r requirements_enhanced.txt")
        return 1

    # Test server
    if not test_server():
        print("\n❌ Setup aborted due to server test failure")
        return 1

    # Setup MCP configuration
    if not setup_claude_code_mcp():
        print("\n❌ Setup aborted due to configuration failure")
        return 1

    # Print usage instructions
    print_usage_instructions()

    print("\n🎉 Setup completed successfully!")
    print("🔄 Please restart Claude Code to use the new MCP server")
    print("📖 See claude_code_setup.md for detailed documentation")

    return 0

if __name__ == "__main__":
    sys.exit(main())