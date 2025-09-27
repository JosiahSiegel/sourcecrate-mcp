"""
Ultra-simple plugin system for PaperezMCP.

This provides the absolute simplest way to add new academic sources:
1. Generate template: create_plugin("my_source")
2. Edit the generated file with your API logic
3. Register: register_plugin("path/to/my_source_plugin.py")

That's it! The source is now available in all searches.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def create_plugin(source_name: str, output_dir: str = ".") -> str:
    """
    Create a simple plugin template.

    Args:
        source_name: Name of the academic source (e.g., "ieee_xplore")
        output_dir: Directory to create the plugin file

    Returns:
        Path to the created plugin file

    Example:
        >>> plugin_path = create_plugin("ieee_xplore")
        >>> # Edit ieee_xplore_plugin.py with your API logic
        >>> register_plugin(plugin_path)
    """
    # Clean source name for Python class/module naming
    class_name = ''.join(word.capitalize() for word in source_name.replace('-', '_').split('_'))
    module_name = source_name.lower().replace('-', '_')

    # Generate simple template
    template = f'''"""
{class_name} plugin for PaperezMCP.

This plugin adds {source_name} as an academic source.
Edit the search method below to implement your API logic.
"""

import asyncio
import logging
from typing import Any, Dict, List

# Import the base client from PaperezMCP
from paperez_mcp.api_clients.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class {class_name}Client(BaseAPIClient):
    """
    {class_name} academic source client.

    This extends BaseAPIClient which provides:
    - Automatic retry logic with exponential backoff
    - Caching with configurable expiration
    - Consistent error handling and logging
    - Search result standardization
    """

    def __init__(self, **config):
        """
        Initialize the {class_name} client.

        Args:
            **config: Configuration from user's config file
                     (e.g., api_key, base_url, timeout, etc.)
        """
        super().__init__("{class_name}", cache_expire=3600)

        # Store configuration
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.{source_name.lower()}.org")
        self.timeout = config.get("timeout", 30)

        # Validate required configuration
        if not self.api_key:
            raise ValueError("api_key is required for {class_name}")

    async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform the actual search. This is where you implement your API logic.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of standardized paper dictionaries with these fields:
            - title: Paper title
            - authors: List of author names
            - abstract: Paper abstract
            - journal: Journal name
            - year: Publication year
            - doi: DOI identifier
            - url: Paper URL
            - pdf_url: Direct PDF URL (if available)
            - citation_count: Citation count (if available)
        """
        # TODO: Replace this with your actual API implementation

        # Example implementation (replace with your API calls):
        import httpx

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Build your API request
                headers = {{"Authorization": f"Bearer {{self.api_key}}"}}
                params = {{
                    "query": query,
                    "limit": limit,
                    "format": "json"
                }}

                # Make the API call
                response = await client.get(
                    f"{{self.base_url}}/search",
                    headers=headers,
                    params=params
                )

                if response.status_code != 200:
                    self.logger.warning(f"API returned {{response.status_code}}: {{response.text}}")
                    return []

                data = response.json()

                # Convert API response to standardized format
                results = []
                for item in data.get("results", []):
                    paper = {{
                        "title": item.get("title", ""),
                        "authors": item.get("authors", []),
                        "abstract": item.get("abstract", ""),
                        "journal": item.get("journal", ""),
                        "year": item.get("year"),
                        "doi": item.get("doi"),
                        "url": item.get("url", ""),
                        "pdf_url": item.get("pdf_url"),
                        "citation_count": item.get("citations", 0)
                    }}
                    results.append(self._standardize_paper(paper))

                return results

        except Exception as e:
            self.logger.error(f"{class_name} search failed: {{e}}")
            return []


# Plugin metadata (required)
PLUGIN_INFO = {{
    "name": "{source_name}",
    "version": "1.0.0",
    "description": "{class_name} academic source integration",
    "author": "Your Name",
    "client_class": "{class_name}Client",
    "required_config": ["api_key"],
    "optional_config": ["base_url", "timeout"]
}}

# Example configuration for users
EXAMPLE_CONFIG = {{
    "{module_name}": {{
        "name": "{source_name}",
        "type": "plugin",
        "enabled": True,
        "module_path": "{module_name}_plugin",
        "class_name": "{class_name}Client",
        "config": {{
            "api_key": "your-api-key-here",
            "base_url": "https://api.{source_name.lower()}.org",
            "timeout": 30
        }}
    }}
}}

if __name__ == "__main__":
    # Simple test to verify the plugin works
    import asyncio

    async def test_plugin():
        # Test with dummy config
        config = {{"api_key": "test-key"}}
        client = {class_name}Client(**config)

        # Test search (will fail with dummy config, but validates structure)
        try:
            results = await client.search("test query", 5)
            print(f"Plugin structure valid. Found {{len(results)}} results.")
        except Exception as e:
            print(f"Plugin structure valid. Test failed as expected: {{e}}")

    asyncio.run(test_plugin())
'''

    # Write plugin file
    output_path = Path(output_dir) / f"{module_name}_plugin.py"
    with open(output_path, 'w') as f:
        f.write(template)

    print(f"✅ Created plugin template: {output_path}")
    print(f"")
    print(f"Next steps:")
    print(f"1. Edit {output_path} and implement your API logic in _perform_search()")
    print(f"2. Test it: python {output_path}")
    print(f"3. Register it: python -c 'from paperez_mcp.plugins.simple import register_plugin; register_plugin(\"{output_path}\")'")
    print(f"")
    print(f"Example configuration for your config file:")
    print(f"```yaml")
    print(f"sources:")
    print(f"  {module_name}:")
    print(f"    name: {source_name}")
    print(f"    type: plugin")
    print(f"    enabled: true")
    print(f"    module_path: {module_name}_plugin")
    print(f"    class_name: {class_name}Client")
    print(f"    config:")
    print(f"      api_key: your-api-key-here")
    print(f"```")

    return str(output_path)


def register_plugin(plugin_file: str) -> bool:
    """
    Register a plugin so it's available in searches.

    Args:
        plugin_file: Path to the plugin Python file

    Returns:
        True if registration successful, False otherwise

    Example:
        >>> register_plugin("ieee_xplore_plugin.py")
        ✅ Plugin registered: ieee_xplore
    """
    try:
        plugin_path = Path(plugin_file).resolve()

        if not plugin_path.exists():
            print(f"❌ Plugin file not found: {plugin_file}")
            return False

        # Load plugin metadata
        import importlib.util
        spec = importlib.util.spec_from_file_location("temp_plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, 'PLUGIN_INFO'):
            print(f"❌ Plugin missing PLUGIN_INFO: {plugin_file}")
            return False

        plugin_info = module.PLUGIN_INFO
        source_name = plugin_info["name"]

        # Copy plugin to user's plugin directory
        user_plugins_dir = Path.home() / ".paperez" / "plugins"
        user_plugins_dir.mkdir(parents=True, exist_ok=True)

        plugin_dest = user_plugins_dir / f"{source_name}_plugin.py"

        import shutil
        shutil.copy2(plugin_path, plugin_dest)

        # Update user configuration
        config_file = Path.home() / ".paperez" / "config" / "config.yaml"

        # Ensure config directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)

        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {"sources": {}}

        if "sources" not in config:
            config["sources"] = {}

        # Add plugin to configuration
        config["sources"][source_name] = {
            "name": source_name,
            "type": "plugin",
            "enabled": True,
            "module_path": str(plugin_dest.stem),
            "class_name": plugin_info["client_class"],
            "config": {
                key: f"your-{key}-here" for key in plugin_info.get("required_config", [])
            }
        }

        # Save updated configuration
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

        print(f"✅ Plugin registered: {source_name}")
        print(f"   Plugin file: {plugin_dest}")
        print(f"   Configuration updated: {config_file}")
        print(f"")
        print(f"⚠️  Don't forget to:")
        print(f"   1. Add your API credentials to {config_file}")
        print(f"   2. Restart PaperezMCP to load the new plugin")

        return True

    except Exception as e:
        print(f"❌ Failed to register plugin: {e}")
        return False


def list_plugins() -> Dict[str, Dict[str, Any]]:
    """
    List all registered plugins.

    Returns:
        Dictionary of plugin information
    """
    plugins = {}

    try:
        user_plugins_dir = Path.home() / ".paperez" / "plugins"

        if not user_plugins_dir.exists():
            return plugins

        for plugin_file in user_plugins_dir.glob("*_plugin.py"):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("temp_plugin", plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, 'PLUGIN_INFO'):
                    plugin_info = module.PLUGIN_INFO
                    plugins[plugin_info["name"]] = {
                        "file": str(plugin_file),
                        "version": plugin_info.get("version", "unknown"),
                        "description": plugin_info.get("description", ""),
                        "author": plugin_info.get("author", "unknown")
                    }
            except Exception as e:
                logger.warning(f"Failed to load plugin {plugin_file}: {e}")

    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")

    return plugins


# Convenience CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m paperez_mcp.plugins.simple create <source_name>")
        print("  python -m paperez_mcp.plugins.simple register <plugin_file>")
        print("  python -m paperez_mcp.plugins.simple list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create" and len(sys.argv) >= 3:
        create_plugin(sys.argv[2])
    elif command == "register" and len(sys.argv) >= 3:
        register_plugin(sys.argv[2])
    elif command == "list":
        plugins = list_plugins()
        if plugins:
            print("Registered plugins:")
            for name, info in plugins.items():
                print(f"  {name} v{info['version']} - {info['description']}")
        else:
            print("No plugins registered.")
    else:
        print("Invalid command. Use create, register, or list.")