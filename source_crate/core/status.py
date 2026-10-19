"""
Core status and help functionality for SourceCrateMCP.

This module contains protocol-agnostic system status and help functions that can
be called from any interface (MCP, HTTP, CLI, etc.).

These adapters normalize the shared research service responses.
"""

import logging
from typing import Any, cast

logger = logging.getLogger(__name__)


async def get_status_core(
    force_reload: bool = False, active_health_check: bool = False
) -> dict[str, Any]:
    """
    Get comprehensive system status including API health and configuration details.

    Reports operational status of all academic databases, detailed health metrics,
    performance data, cache usage, and comprehensive configuration details.

    Args:
        force_reload: If True, force reload configuration before checking status.
                     Useful when custom configs added after server startup.
        active_health_check: If True, perform real-time health checks on all sources (30+ seconds).
                            By default (False), returns cached metrics for instant response.

    Returns:
        Dict containing:
        - api_status: Basic status of all academic database APIs
        - cache_stats: Cache usage and configuration information
        - config: Comprehensive configuration details including categories and sources
        - health_report: Detailed health monitoring with performance metrics
        - recommendations: Specific recommendations for system improvements
        - monitoring_enabled: Whether health monitoring is active
    """
    from source_crate.core import research

    result = await research.get_status(force_reload, active_health_check)
    return cast(dict[str, Any], result)


async def get_help_core() -> dict[str, Any]:
    """
    Get comprehensive configuration guidance and help for SourceCrateMCP.

    Provides detailed instructions on how to create configuration files, including
    file paths, schemas, available options, and examples for customizing the system.

    Returns:
        Dict containing:
        - config_guide: Complete configuration setup guide
        - file_paths: Required file paths for configuration
        - schema_info: Configuration schema and structure
        - examples: Common configuration examples
        - troubleshooting: Common issues and solutions
    """
    from source_crate.core import research

    result = await research.get_help()
    return cast(dict[str, Any], result)
