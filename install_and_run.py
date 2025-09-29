#!/usr/bin/env python
"""Auto-installer and launcher for paperez-mcp

This script handles all setup automatically:
1. Checks/creates virtual environment
2. Installs/updates dependencies
3. Launches the actual server

Benefits:
- Zero manual setup required
- Isolated environment prevents conflicts
- Works across platforms (Windows/Mac/Linux)
- Dependencies cached after first run
"""

import os
import subprocess
import sys
import venv
import shutil
from pathlib import Path


def log(message: str) -> None:
    """Print a log message."""
    print(f"[PaperezMCP Setup] {message}", flush=True)


def get_venv_path() -> Path:
    """Get the path to the virtual environment."""
    repo_root = Path(__file__).parent

    # For GitHub/uvx installations, use a cache-friendly location
    # Check if we're in a uvx cache or temporary directory
    if "uvx-cache" in str(repo_root) or "tmp" in str(repo_root):
        # Use user cache directory for persistent venv
        import tempfile
        cache_dir = Path(tempfile.gettempdir()) / "paperez-mcp-cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / ".venv"

    # For local development, use local .venv
    return repo_root / ".venv"


def get_python_executable(venv_path: Path) -> Path:
    """Get the Python executable path for the current platform."""
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"

    return python_path


def get_pip_executable(venv_path: Path) -> Path:
    """Get the pip executable path for the current platform."""
    # Check both possible locations
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"

    # If standard path doesn't exist, try the other platform's path
    # (handles case where we're in WSL/container but venv was created on Windows)
    if not pip_path.exists():
        if sys.platform == "win32":
            alt_pip = venv_path / "bin" / "pip"
        else:
            alt_pip = venv_path / "Scripts" / "pip.exe"

        if alt_pip.exists():
            return alt_pip

    return pip_path


def create_virtual_environment(venv_path: Path) -> None:
    """Create a virtual environment if it doesn't exist."""
    if venv_path.exists():
        # Check if venv is valid
        python_exe = get_python_executable(venv_path)
        if python_exe.exists():
            log("Virtual environment already exists")
            return
        else:
            log("Virtual environment corrupted, recreating...")
            shutil.rmtree(venv_path, ignore_errors=True)

    log("Creating virtual environment...")
    try:
        venv.create(venv_path, with_pip=True, clear=True, symlinks=False)
        log("Virtual environment created successfully")
    except Exception as e:
        log(f"Failed to create venv: {e}")
        raise


def is_already_installed() -> bool:
    """Check if paperez-mcp is already installed in the current Python environment."""
    try:
        import paperez_mcp
        log("PaperezMCP already installed in current environment")
        return True
    except ImportError:
        return False


def install_dependencies(venv_path: Path) -> None:
    """Install dependencies in the virtual environment."""
    repo_root = Path(__file__).parent
    python_executable = get_python_executable(venv_path)

    if not python_executable.exists():
        log(f"Python executable not found at {python_executable}")
        raise FileNotFoundError(f"Python not found at {python_executable}")

    # Use python -m pip which is more reliable
    pip_cmd = [str(python_executable), "-m", "pip"]

    # Upgrade pip first
    log("Upgrading pip...")
    try:
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"],
                      capture_output=True, text=True, timeout=60)
    except Exception as e:
        log(f"Warning: Failed to upgrade pip: {e}")

    log("Installing dependencies...")

    # Try multiple installation strategies
    installation_strategies = [
        # Strategy 1: Install from local pyproject.toml (development)
        lambda: subprocess.run(
            pip_cmd + ["install", "-e", str(repo_root)],
            capture_output=True, text=True, timeout=300
        ),
        # Strategy 2: Install directly from GitHub (production)
        lambda: subprocess.run(
            pip_cmd + ["install", "git+https://github.com/JosiahSiegel/paperez-mcp.git"],
            capture_output=True, text=True, timeout=300
        ),
        # Strategy 3: Install from current directory as package
        lambda: subprocess.run(
            pip_cmd + ["install", str(repo_root)],
            capture_output=True, text=True, timeout=300
        ),
    ]

    for i, strategy in enumerate(installation_strategies, 1):
        try:
            log(f"Trying installation strategy {i}...")
            result = strategy()

            if result.returncode == 0:
                log(f"Dependencies installed successfully (strategy {i})")
                return
            else:
                log(f"Strategy {i} failed: {result.stderr}")

        except Exception as e:
            log(f"Strategy {i} failed with exception: {e}")

    # Fallback: Install core dependencies manually
    core_deps = [
        "fastmcp>=2.12.0",
        "scholarly>=1.7.11",
        "PyMuPDF>=1.23.0",
        "pymupdf4llm>=0.0.17",
        "httpx[http2]>=0.25.0",
        "aiohttp>=3.8.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "arxiv>=2.0.0",
        "pymed>=0.8.9",
        "semanticscholar>=0.8.0",
        "tenacity>=8.2.0",
        "diskcache>=5.6.0",
        "asyncio-throttle>=1.0.2",
        "fake-useragent>=1.4.0",
        "free-proxy>=1.1.1",
        "pdfplumber>=0.10.0"
    ]

    log("Installing core dependencies manually...")
    failed_deps = []

    for dep in core_deps:
        try:
            result = subprocess.run(
                pip_cmd + ["install", dep],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                log(f"✓ Installed {dep}")
            else:
                failed_deps.append(dep)
                log(f"✗ Failed to install {dep}")
        except Exception as e:
            failed_deps.append(dep)
            log(f"✗ Error installing {dep}: {e}")

    if failed_deps:
        log(f"Warning: Some dependencies failed to install: {', '.join(failed_deps)}")
        log("The server may not work correctly.")


def launch_server(venv_path: Path) -> None:
    """Launch the paperez-mcp server."""
    repo_root = Path(__file__).parent
    python_executable = get_python_executable(venv_path)
    server_script = repo_root / "paperez_mcp" / "server.py"

    if not server_script.exists():
        log(f"Server script not found at {server_script}")
        sys.exit(1)

    log("Launching PaperezMCP server...")

    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)

    # Execute the server
    try:
        subprocess.run([str(python_executable), str(server_script)], env=env, check=False)
    except KeyboardInterrupt:
        log("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        log(f"Server failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    try:
        # # Check if we're already in a properly configured environment
        # if is_already_installed():
        #     # Try to run directly without creating venv
        #     try:
        #         repo_root = Path(__file__).parent
        #         server_script = repo_root / "paperez_mcp" / "server.py"

        #         if server_script.exists():
        #             log("Running from current environment...")
        #             # Set up environment
        #             env = os.environ.copy()
        #             env["PYTHONPATH"] = str(repo_root)

        #             # Execute the server directly
        #             subprocess.run([sys.executable, str(server_script)], env=env, check=False)
        #             return
        #     except Exception as e:
        #         log(f"Direct execution failed: {e}, falling back to venv setup")

        # Always use venv setup to ensure all dependencies are available
        venv_path = get_venv_path()

        # Step 1: Create virtual environment
        create_virtual_environment(venv_path)

        # Step 2: Install dependencies
        install_dependencies(venv_path)

        # Step 3: Launch server
        launch_server(venv_path)

    except Exception as e:
        log(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()