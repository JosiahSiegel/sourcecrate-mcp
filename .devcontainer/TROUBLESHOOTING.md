# Devcontainer Troubleshooting Guide

## Port Forwarding Issues (ERR_CONNECTION_RESET)

### Problem: Browser shows `ERR_CONNECTION_RESET` when accessing `http://localhost:9000`

The UI correctly detects the API should be at `localhost:9000`, but the Windows browser cannot connect.

### Root Cause

On WSL2/Docker Desktop, `--network=host` does not work. VS Code must forward ports from the container to Windows.

### Solution Steps

1. **Check VS Code's PORTS panel:**
   - Press `Ctrl+Shift+P` → "Ports: Focus on Ports View"
   - Verify these ports are forwarded:
     - Port 9000 → localhost:9000 (HTTP API)
     - Port 3001 → localhost:3001 (Browser UI)

2. **If port 9000 is NOT listed:**
   - The API process may not be running
   - Start it manually: `bash scripts/local-manager.sh http-start`
   - Or restart the devcontainer: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

3. **If port 9000 shows different Windows port:**
   - Example: Port 9000 forwarded to localhost:9001 ❌
   - This means Windows port 9000 was already taken by another process
   - Right-click the port → "Change Local Address Port"
   - Set it to 9000 (if available)
   - Or configure requireLocalPort in `.vscode/settings.json` (already set)

4. **Test connection from inside container:**
   ```bash
   # Should return {"status":"healthy"}
   curl http://localhost:9000/health
   ```

5. **Test connection from Windows:**
   - Open `http://localhost:9000/health` in browser
   - Should show: `{"status":"healthy","service":"sourcecrate-mcp"}`

### Quick Fix: Restart Port Forwarding

1. In VS Code PORTS panel, right-click port 9000
2. Click "Stop Forwarding Port"
3. Wait 2 seconds
4. Port should auto-forward again when API is detected

### Alternative: Use Different Port

If Windows port 9000 is taken by another service:

1. Stop the API: `bash scripts/local-manager.sh http-stop`
2. Start on different port: `HTTP_PORT=9001 bash scripts/local-manager.sh http-start`
3. Update browser-ui: `cd browser-ui && echo "window.PAPEREZ_API_URL = 'http://localhost:9001';" > config.js`
4. Refresh browser

## Common Issues

### Issue: "No app selected" in fly-manager.sh

**Solution:** The script will auto-select if you only have one app, or prompt you to choose.

### Issue: Python dependencies not found

**Solution:**
```bash
# Install dev dependencies
uv pip install -e .[dev,http]

# Or use uvx (recommended)
uvx --from '.[http]' sourcecrate-http
```

### Issue: Port already in use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution:**
```bash
# Find process using port 9000
lsof -i :9000

# Kill it
kill <PID>

# Or use a different port
HTTP_PORT=9001 bash scripts/local-manager.sh http-start
```

### Issue: Changes not reflected after restart

**Solution:**
- For MCP server changes: Restart Claude Code entirely
- For HTTP server changes: `bash scripts/local-manager.sh http-stop && bash scripts/local-manager.sh http-start`
- For browser UI changes: Hard refresh browser (`Ctrl+Shift+R`)

## Verifying Port Forwarding

Run this inside the devcontainer:

```bash
# Check what's running
ps aux | grep -E 'sourcecrate|python.*http'

# Check ports
lsof -i :9000 -i :3001 2>/dev/null || ss -tln | grep -E ':(9000|3001)'

# Test API
curl http://localhost:9000/health

# Check VS Code settings
cat ~/.vscode-server/data/Machine/settings.json | grep -A 10 "remote.portsAttributes"
```

Expected output:
```
PID running sourcecrate-http on port 9000 ✓
PID running python http.server on port 3001 ✓
API health check returns {"status":"healthy"} ✓
VS Code has portsAttributes for 9000, 3000, 3001 ✓
```

## Docker Desktop + WSL2 Specific Issues

### Network Mode Limitations

- `--network=host` **DOES NOT WORK** on Windows/Mac Docker Desktop
- Only works on native Linux Docker
- VS Code handles port forwarding via `forwardPorts` configuration

### Why This Matters

The devcontainer.json previously used `--network=host`, which:
- Works on Linux (direct network access)
- Fails silently on WSL2 (ports not accessible from Windows)
- Has been removed in favor of VS Code's automatic port forwarding

### Manual Port Forwarding (If Auto-Forward Fails)

1. Open `.devcontainer/devcontainer.json`
2. Ensure `forwardPorts` includes your ports:
   ```json
   {
     "forwardPorts": [9000, 3000, 3001]
   }
   ```
3. Rebuild container: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

## Getting Help

If port forwarding still doesn't work:

1. Check VS Code's Output panel: `Ctrl+Shift+P` → "Output" → "Dev Containers"
2. Look for port forwarding errors
3. Verify Docker Desktop is running
4. Restart Docker Desktop
5. Rebuild devcontainer: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"
