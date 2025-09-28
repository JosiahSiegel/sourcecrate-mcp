"""
Configuration manager for PaperezMCP - Multi-tier config loading with hot-reloading.
Handles default configs, user configs, and environment overrides.
"""

import logging
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

# Optional watchdog dependency for hot-reloading
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from .schemas import PaperezConfig

logger = logging.getLogger(__name__)


if WATCHDOG_AVAILABLE:
    class ConfigFileHandler(FileSystemEventHandler):
        """File system event handler for configuration hot-reloading."""

        def __init__(self, config_manager: 'ConfigManager'):
            self.config_manager = config_manager
            self.debounce_time = 1.0  # seconds
            self.last_reload = 0.0

        def on_modified(self, event: Any) -> None:
            if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
                # Debounce rapid file changes
                current_time = time.time()
                if current_time - self.last_reload > self.debounce_time:
                    self.last_reload = current_time
                    logger.info(f"Config file changed: {event.src_path}")
                    self.config_manager._reload_config()
else:
    # Dummy handler when watchdog is not available
    class DummyConfigFileHandler:
        def __init__(self, config_manager: Any) -> None:
            pass

    # Alias for compatibility
    ConfigFileHandler = DummyConfigFileHandler  # type: ignore[misc,assignment]


class ConfigManager:
    """
    Manages PaperezMCP configuration with multi-tier loading and hot-reloading.

    Loads ALL YAML files from configuration directories for organized config management.

    Configuration priority (highest to lowest):
    1. Environment variables (PAPEREZ_*)
    2. Environment config file (PAPEREZ_CONFIG_PATH)
    3. Local project config directory (./.paperez/config/*.yaml)
    4. User home config directory (~/.paperez/config/*.yaml)
    5. Built-in defaults directory (.paperez/config/*.yaml)

    All YAML files in each directory are loaded and merged together.
    """

    def __init__(self, enable_hot_reload: bool = True):
        # Disable hot-reload if watchdog is not available
        if enable_hot_reload and not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available - disabling hot-reload functionality")
            enable_hot_reload = False

        self.enable_hot_reload = enable_hot_reload
        self._config: PaperezConfig | None = None
        self._config_lock = threading.RLock()
        self._observers: list = []  # List[Observer] when watchdog available
        self._reload_callbacks: list[Callable[[PaperezConfig], None]] = []

        # Configuration directory paths (load ALL YAML files from these directories)
        # Get the root directory of the paperez-mcp package
        package_root = Path(__file__).parent.parent.parent
        self.config_directories = {
            'mcp_default': package_root / '.paperez' / 'config',
            'user_home': Path.home() / '.paperez' / 'config',
            'project_local': Path.cwd() / '.paperez' / 'config',
        }

        # Legacy single file paths for backward compatibility and environment override
        self.config_paths = {
            'environment': self._get_env_config_path(),
            'user_home': Path.home() / ".paperez" / "config" / "config.yaml"
        }

        self._load_config()
        if self.enable_hot_reload and WATCHDOG_AVAILABLE:
            self._setup_file_watching()

    def _get_env_config_path(self) -> Path | None:
        """Get configuration path from environment variable."""
        env_path = os.getenv('PAPEREZ_CONFIG_PATH')
        return Path(env_path) if env_path else None

    def _load_config(self) -> None:
        """Load and merge configuration from all sources (directories and individual files)."""
        with self._config_lock:
            try:
                # Check if user wants to disable default sources by checking all config directories
                use_defaults = True
                for layer_name, config_dir in self.config_directories.items():
                    if layer_name == 'mcp_default':
                        continue  # Don't check default config for this setting

                    if config_dir.exists():
                        dir_config = self._load_yaml_directory(config_dir)
                        if dir_config.get('use_default_sources') is False:
                            use_defaults = False
                            logger.info(f"Default sources disabled by config in {config_dir}")
                            break

                # Also check environment file
                if self.config_paths.get('environment'):
                    env_path = self.config_paths['environment']
                    if env_path and env_path.exists():
                        try:
                            env_config = self._load_yaml_file(env_path)
                            if env_config.get('use_default_sources') is False:
                                use_defaults = False
                                logger.info(f"Default sources disabled by environment config: {env_path}")
                        except Exception as e:
                            logger.debug(f"Failed to check use_default_sources in environment config: {e}")

                # Start with base configuration
                config_dict = {}

                if use_defaults:
                    # Load MCP default directory (all YAML files)
                    mcp_default_dir = self.config_directories['mcp_default']
                    if mcp_default_dir.exists():
                        config_dict = self._load_yaml_directory(mcp_default_dir)
                        logger.info(f"Loaded MCP default config directory: {mcp_default_dir}")
                    else:
                        logger.error(f"MCP default config directory not found: {mcp_default_dir}")
                        # Ultimate fallback
                        config_dict = {
                            'version': '1.0',
                            'default_category': None,
                            'sources': {},
                            'categories': {}
                        }
                else:
                    # User disabled defaults - start with minimal config
                    config_dict = {
                        'version': '1.0',
                        'default_category': None,
                        'sources': {},
                        'categories': {},
                        'use_default_sources': False
                    }
                    logger.info("Default sources disabled - starting with minimal config")

                # Load and merge each configuration directory (in priority order)
                config_layers = [
                    ('user_home', self.config_directories['user_home']),
                    ('project_local', self.config_directories['project_local'])
                ]

                for layer_name, config_dir in config_layers:
                    if config_dir.exists():
                        try:
                            layer_config = self._load_yaml_directory(config_dir)
                            if layer_config:  # Only merge if directory had content
                                config_dict = self._smart_merge(config_dict, layer_config)
                                logger.info(f"Merged config directory: {layer_name} ({config_dir})")
                        except Exception as e:
                            logger.warning(f"Failed to load config directory {layer_name}: {e}")

                # Load individual environment file if specified
                if self.config_paths.get('environment'):
                    env_path = self.config_paths['environment']
                    if env_path and env_path.exists():
                        try:
                            env_config = self._load_yaml_file(env_path)
                            config_dict = self._smart_merge(config_dict, env_config)
                            logger.info(f"Loaded environment config file: {env_path}")
                        except Exception as e:
                            logger.warning(f"Failed to load environment config: {e}")

                # Apply environment variable overrides
                env_overrides = self._get_env_overrides()
                if env_overrides:
                    config_dict = self._deep_merge(config_dict, env_overrides)
                    logger.info("Applied environment variable overrides")

                # Validate and create Pydantic model
                self._config = PaperezConfig(**config_dict)

                # Validate configuration and log warnings
                warnings = self._config.validate_configuration()
                for warning in warnings:
                    logger.warning(f"Config validation: {warning}")

                logger.info("Configuration loaded successfully")

            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                # Fall back to minimal configuration
                fallback_config: dict[str, Any] = {
                    'version': '1.0',
                    'default_category': None,
                    'sources': {},
                    'categories': {}
                }
                self._config = PaperezConfig(**fallback_config)

    def _load_yaml_file(self, file_path: Path) -> dict[str, Any]:
        """Load YAML configuration file."""
        with open(file_path, encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _load_yaml_directory(self, directory_path: Path) -> dict[str, Any]:
        """Load and merge all YAML files from a directory."""
        if not directory_path.exists() or not directory_path.is_dir():
            return {}

        merged_config: dict[str, Any] = {}
        yaml_files: list[Path] = []

        # Find all YAML files in the directory
        for pattern in ['*.yaml', '*.yml']:
            yaml_files.extend(directory_path.glob(pattern))

        # Exclude special files that shouldn't be part of regular config loading
        excluded_files = {'config.yaml', 'minimal_config.yaml'}
        yaml_files = [f for f in yaml_files if f.name not in excluded_files]

        # Sort files to ensure consistent loading order
        yaml_files.sort()

        for yaml_file in yaml_files:
            try:
                file_config = self._load_yaml_file(yaml_file)
                merged_config = self._deep_merge(merged_config, file_config)
                logger.debug(f"Loaded config file: {yaml_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {yaml_file}: {e}")

        if yaml_files:
            logger.info(f"Loaded {len(yaml_files)} YAML files from {directory_path}")

        return merged_config

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            elif key in result and result[key] is None and isinstance(value, dict):
                # Handle case where base has None but override has a dict (e.g., sources, categories)
                result[key] = value
            elif key not in result and isinstance(value, dict):
                # Initialize missing dict keys
                result[key] = value
            else:
                result[key] = value

        return result

    def _smart_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Smart merge that applies normal deep merge (same names override, new names merge)."""
        return self._deep_merge(base, override)

    def _get_env_overrides(self) -> dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides: dict[str, Any] = {}

        # Map environment variables to config paths
        env_mappings = {
            'PAPEREZ_DEFAULT_CATEGORY': ['default_category'],
            'PAPEREZ_CACHE_ENABLED': ['global_cache_enabled'],
            'PAPEREZ_CACHE_EXPIRE': ['global_cache_expire'],
            'PAPEREZ_OUTPUT_DIR': ['default_output_dir'],
            'PAPEREZ_MAX_CONCURRENT': ['max_concurrent_searches'],
            'PAPEREZ_USE_DEFAULT_SOURCES': ['use_default_sources'],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Type conversion
                value: str | bool | int
                if env_var.endswith('_ENABLED'):
                    value = env_value.lower() in ('true', '1', 'yes', 'on')
                elif env_var.endswith('_EXPIRE') or env_var.endswith('_CONCURRENT'):
                    try:
                        value = int(env_value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_var}: {env_value}")
                        continue
                else:
                    value = env_value

                # Set nested value
                current = overrides
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = value

        return overrides

    def _setup_file_watching(self) -> None:
        """Setup file system watching for hot-reloading."""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available - file watching disabled")
            return

        # Watch all config directories
        for layer_name, config_dir in self.config_directories.items():
            if layer_name == 'mcp_default':
                continue  # Don't watch the built-in default config

            if config_dir.exists():
                observer = Observer()
                handler = ConfigFileHandler(self)
                observer.schedule(handler, str(config_dir), recursive=False)
                observer.start()
                self._observers.append(observer)
                logger.info(f"Watching config directory: {config_dir}")

        # Also watch individual environment file if specified
        if self.config_paths.get('environment'):
            env_path = self.config_paths['environment']
            if env_path and env_path.exists():
                observer = Observer()
                handler = ConfigFileHandler(self)
                observer.schedule(handler, str(env_path.parent), recursive=False)
                observer.start()
                self._observers.append(observer)
                logger.info(f"Watching environment config file: {env_path}")

    def _reload_config(self) -> None:
        """Reload configuration and notify callbacks."""
        logger.info("Reloading configuration...")
        self._load_config()

        # Notify callbacks of config change
        if self._config is not None:
            for callback in self._reload_callbacks:
                try:
                    callback(self._config)
                except Exception as e:
                    logger.error(f"Error in config reload callback: {e}")

        logger.info("Configuration reloaded successfully")

    def get_config(self) -> PaperezConfig:
        """Get current configuration."""
        with self._config_lock:
            if self._config is None:
                # Force configuration load if not already loaded
                self._load_config()
            return self._config  # type: ignore  # _load_config ensures this is not None

    def add_reload_callback(self, callback: Callable[[PaperezConfig], None]) -> None:
        """Add callback to be called when configuration is reloaded."""
        self._reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: Callable[[PaperezConfig], None]) -> None:
        """Remove reload callback."""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)

    def save_user_config(self, config: dict[str, Any]) -> None:
        """Save configuration to user home directory."""
        user_config_path = self.config_paths['user_home']
        assert user_config_path is not None  # We explicitly set this in __init__
        user_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(user_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

        logger.info(f"Saved user configuration to {user_config_path}")

    def create_example_config(self, output_path: Path) -> None:
        """Create an example configuration file."""
        example_config = {
            'version': '1.0',
            'default_category': 'comprehensive',
            'routing': {
                'enabled': True,
                'fallback_enabled': True
            },
            'categories': {
                'my_custom_category': {
                    'name': 'my_custom_category',
                    'display_name': 'My Custom Category',
                    'description': 'Custom category for specific research needs',
                    'type': 'standard',
                    'sources': ['crossref', 'arxiv']
                },
                'ai_comprehensive': {
                    'name': 'ai_comprehensive',
                    'display_name': 'AI Research (Comprehensive)',
                    'description': 'Meta-category for AI research across multiple sources',
                    'type': 'meta',
                    'includes': ['preprints', 'journals', 'medical'],
                    'merge_strategy': 'weighted_union',
                    'weights': {
                        'preprints': 0.5,
                        'journals': 0.3,
                        'medical': 0.2
                    }
                }
            },
            'sources': {
                'my_university_repo': {
                    'name': 'my_university_repo',
                    'type': 'plugin',
                    'enabled': True,
                    'module_path': 'my_plugins.university_repo',
                    'class_name': 'UniversityRepoClient',
                    'config': {
                        'api_key': 'your-api-key-here',
                        'base_url': 'https://repo.university.edu/api'
                    }
                }
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(example_config, f, default_flow_style=False, indent=2)

        logger.info(f"Created example configuration at {output_path}")

    def shutdown(self) -> None:
        """Shutdown the configuration manager and stop file watching."""
        if WATCHDOG_AVAILABLE:
            for observer in self._observers:
                observer.stop()
                observer.join()
        self._observers.clear()
        logger.info("Configuration manager shutdown")

    def __enter__(self) -> 'ConfigManager':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()


# Global configuration manager instance
_config_manager: ConfigManager | None = None


def get_config_manager(enable_hot_reload: bool = True) -> ConfigManager:
    """Get or create the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(enable_hot_reload=enable_hot_reload)
    return _config_manager


def get_current_config() -> PaperezConfig:
    """Get the current configuration."""
    return get_config_manager().get_config()
