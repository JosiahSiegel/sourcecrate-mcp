# MCP Troubleshooting Guide

## Issue: `/mcp` command returns no content in Claude Code

### Quick Fixes to Try

#### 1. Check Dependencies First
```bash
# Verify Python dependencies are installed
pip install fastmcp scholarly httpx aiohttp requests PyMuPDF lxml
```

#### 2. Test Server Directly
```bash
# Test if the server can start
python3 scholarly_enhanced_server.py
```

#### 3. Manual Server Registration in Claude Code

Try adding the server manually with the `/mcp add` command:

```bash
/mcp add scholarly-enhanced python3 scholarly_enhanced_server.py --cwd /mnt/d/repos/scholarly-mcp
```

Or for GitHub URL deployment:
```bash
/mcp add scholarly-enhanced fastmcp run https://github.com/your-username/scholarly-mcp.git --entrypoint scholarly_enhanced_server.py:mcp
```

#### 4. Check Claude Code MCP Status
```bash
/doctor
```

This will show if MCP is properly configured in Claude Code.

#### 5. Alternative: Direct FastMCP Usage

If the above doesn't work, try using FastMCP directly:

```bash
# Install FastMCP if not already installed
pip install fastmcp

# Run the server directly
fastmcp run scholarly_enhanced_server.py:mcp
```

### Common Issues and Solutions

#### Issue: "No module named 'fastmcp'"
**Solution**: Install FastMCP
```bash
pip install fastmcp
```

#### Issue: "No module named 'scholarly'"
**Solution**: Install all dependencies
```bash
pip install -r requirements_enhanced.txt
```

#### Issue: "Server not found"
**Solution**: Check working directory
```bash
# Make sure you're in the right directory
pwd
# Should show: /mnt/d/repos/scholarly-mcp

# List files to verify
ls -la scholarly_enhanced_server.py
```

#### Issue: "Import errors"
**Solution**: Test imports manually
```bash
python3 -c "import fastmcp; import scholarly; print('All imports work!')"
```

### Alternative Deployment Methods

#### Method 1: Use the Basic Server (Fewer Dependencies)
If the enhanced server has issues, try the basic one:

```bash
/mcp add scholarly-basic python3 scholarly_server.py --cwd /mnt/d/repos/scholarly-mcp
```

**Note**: You'll need to create `scholarly_server.py` with just the basic tools (no PDF processing).

#### Method 2: Use HTTP Transport
Start the server with HTTP transport:

```bash
python3 -c "
from scholarly_enhanced_server import mcp
mcp.run(transport='http', port=8000)
"
```

Then connect via HTTP URL in Claude Code.

#### Method 3: Deploy to FastMCP Cloud
1. Push this repository to GitHub
2. Deploy to FastMCP Cloud
3. Use the resulting HTTPS URL in Claude Code

### Verification Steps

Once you get MCP working, verify with these commands:

```bash
# List available servers
/mcp list

# Test a simple tool
/mcp call scholarly-enhanced search_author '{"name": "Geoffrey Hinton", "limit": 1}'

# Test full-text retrieval (if working)
/mcp call scholarly-enhanced get_full_text_by_title '{"title": "Attention Is All You Need", "extract_text": true}'
```

### Debug Information

If you're still having issues, run this debug script:

```bash
python3 -c "
import sys
import os
print(f'Python path: {sys.executable}')
print(f'Working directory: {os.getcwd()}')
print(f'Python version: {sys.version}')

try:
    import fastmcp
    print(f'FastMCP version: {fastmcp.__version__}')
except ImportError as e:
    print(f'FastMCP import error: {e}')

try:
    import scholarly
    print('Scholarly imported successfully')
except ImportError as e:
    print(f'Scholarly import error: {e}')

# Check if server file exists
if os.path.exists('scholarly_enhanced_server.py'):
    print('✅ Server file found')
else:
    print('❌ Server file not found')
"
```

### Last Resort: Minimal Working Example

If nothing else works, try this minimal MCP server:

```python
# Create minimal_server.py
from fastmcp import FastMCP

mcp = FastMCP("Minimal Test Server")

@mcp.tool
def hello(name: str) -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
```

Then add it to Claude Code:
```bash
/mcp add test-server python3 minimal_server.py --cwd /mnt/d/repos/scholarly-mcp
```

If this works, the issue is with the enhanced server dependencies.