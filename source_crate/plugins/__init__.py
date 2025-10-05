"""
Simple Plugin System for SourceCrateMCP

The easiest way to add new academic sources to SourceCrateMCP.

Usage:
    from source_crate.plugins.simple import create_plugin, register_plugin

    # Create a new plugin
    create_plugin("my_source")

    # Install it
    register_plugin("my_source_plugin.py")

Or use the CLI:
    ./scripts/sourcecrate-plugin create my_source
    ./scripts/sourcecrate-plugin install my_source_plugin.py
"""

from .simple import create_plugin, list_plugins, register_plugin

__all__ = ["create_plugin", "register_plugin", "list_plugins"]
