"""
Configuration manager for PaperezMCP - Multi-tier config loading with hot-reloading.
Handles default configs, user configs, and environment overrides.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import threading
import time

# Optional watchdog dependency for hot-reloading
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
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
            self.last_reload = 0

        def on_modified(self, event):
            if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
                # Debounce rapid file changes
                current_time = time.time()
                if current_time - self.last_reload > self.debounce_time:
                    self.last_reload = current_time
                    logger.info(f"Config file changed: {event.src_path}")
                    self.config_manager._reload_config()
else:
    # Dummy handler when watchdog is not available
    class ConfigFileHandler:
        def __init__(self, config_manager):
            pass


class ConfigManager:
    """
    Manages PaperezMCP configuration with multi-tier loading and hot-reloading.

    Configuration priority (highest to lowest):
    1. Environment variables (PAPEREZ_*)
    2. Local project config (./paperez.config.yaml)
    3. User home config (~/.paperez/config.yaml)
    4. Built-in defaults
    """

    def __init__(self, enable_hot_reload: bool = True):
        # Disable hot-reload if watchdog is not available
        if enable_hot_reload and not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available - disabling hot-reload functionality")
            enable_hot_reload = False

        self.enable_hot_reload = enable_hot_reload
        self._config: Optional[PaperezConfig] = None
        self._config_lock = threading.RLock()
        self._observers: List = []  # List[Observer] when watchdog available
        self._reload_callbacks: List[Callable[[PaperezConfig], None]] = []

        # Configuration file paths
        self.config_paths = {
            'builtin': Path(__file__).parent / 'default_config.yaml',
            'user_home': Path.home() / '.paperez' / 'config.yaml',
            'project_local': Path.cwd() / 'paperez.config.yaml',
            'environment': self._get_env_config_path()
        }

        self._load_config()
        if self.enable_hot_reload and WATCHDOG_AVAILABLE:
            self._setup_file_watching()

    def _get_env_config_path(self) -> Optional[Path]:
        """Get configuration path from environment variable."""
        env_path = os.getenv('PAPEREZ_CONFIG_PATH')
        return Path(env_path) if env_path else None

    def _load_config(self):
        """Load and merge configuration from all sources."""
        with self._config_lock:
            try:
                # Start with default configuration from YAML
                config_dict = {}
                builtin_path = self.config_paths['builtin']
                if builtin_path.exists():
                    config_dict = self._load_yaml_file(builtin_path)
                    logger.info(f"Loaded builtin config: {builtin_path}")
                else:
                    logger.error(f"Builtin config not found: {builtin_path}")
                    # Fallback to minimal config
                    config_dict = {
                        'version': '1.0',
                        'default_category': 'comprehensive',
                        'sources': {},
                        'categories': {}
                    }

                # Load and merge each configuration layer
                for layer_name, config_path in self.config_paths.items():
                    if layer_name == 'builtin':
                        continue  # Already loaded

                    if config_path and config_path.exists():
                        try:
                            layer_config = self._load_yaml_file(config_path)
                            config_dict = self._smart_merge(config_dict, layer_config)
                            logger.info(f"Loaded config layer: {layer_name} ({config_path})")
                        except Exception as e:
                            logger.warning(f"Failed to load config layer {layer_name}: {e}")

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
                fallback_config = {
                    'version': '1.0',
                    'default_category': 'comprehensive',
                    'sources': {},
                    'categories': {}
                }
                self._config = PaperezConfig(**fallback_config)

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _smart_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Smart merge that respects user control options for sources."""
        result = base.copy()

        # Check user control options in override
        use_default_sources = override.get('use_default_sources', True)
        merge_user_sources = override.get('merge_user_sources', True)

        for key, value in override.items():
            if key == 'sources':
                # Handle source merging based on user preferences
                if not use_default_sources:
                    # User wants to disable all default sources, use only user sources
                    result[key] = value
                elif not merge_user_sources:
                    # User wants to replace (not merge) sources
                    result[key] = value
                else:
                    # Default behavior: merge user sources with defaults
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = self._deep_merge(result[key], value)
                    else:
                        result[key] = value
            elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _get_env_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides = {}

        # Map environment variables to config paths
        env_mappings = {
            'PAPEREZ_DEFAULT_CATEGORY': ['default_category'],
            'PAPEREZ_CACHE_ENABLED': ['global_cache_enabled'],
            'PAPEREZ_CACHE_EXPIRE': ['global_cache_expire'],
            'PAPEREZ_OUTPUT_DIR': ['default_output_dir'],
            'PAPEREZ_MAX_CONCURRENT': ['max_concurrent_searches'],
            'PAPEREZ_USE_DEFAULT_SOURCES': ['use_default_sources'],
            'PAPEREZ_MERGE_USER_SOURCES': ['merge_user_sources'],
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if env_var.endswith('_ENABLED'):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif env_var.endswith('_EXPIRE') or env_var.endswith('_CONCURRENT'):
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_var}: {value}")
                        continue

                # Set nested value
                current = overrides
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = value

        return overrides

    def _setup_file_watching(self):
        """Setup file system watching for hot-reloading."""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available - file watching disabled")
            return

        for layer_name, config_path in self.config_paths.items():
            if layer_name == 'builtin' or not config_path:
                continue

            if config_path.exists():
                observer = Observer()
                handler = ConfigFileHandler(self)
                observer.schedule(handler, str(config_path.parent), recursive=False)
                observer.start()
                self._observers.append(observer)
                logger.info(f"Watching config file: {config_path}")

    def _reload_config(self):
        """Reload configuration and notify callbacks."""
        logger.info("Reloading configuration...")
        old_config = self._config
        self._load_config()

        # Notify callbacks of config change
        for callback in self._reload_callbacks:
            try:
                callback(self._config)
            except Exception as e:
                logger.error(f"Error in config reload callback: {e}")

        logger.info("Configuration reloaded successfully")

    def get_config(self) -> PaperezConfig:
        """Get current configuration."""
        with self._config_lock:
            return self._config

    def add_reload_callback(self, callback: Callable[[PaperezConfig], None]):
        """Add callback to be called when configuration is reloaded."""
        self._reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: Callable[[PaperezConfig], None]):
        """Remove reload callback."""
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)

    def save_user_config(self, config: Dict[str, Any]):
        """Save configuration to user home directory."""
        user_config_path = self.config_paths['user_home']
        user_config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(user_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

        logger.info(f"Saved user configuration to {user_config_path}")

    def create_example_config(self, output_path: Path):
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

    def shutdown(self):
        """Shutdown the configuration manager and stop file watching."""
        if WATCHDOG_AVAILABLE:
            for observer in self._observers:
                observer.stop()
                observer.join()
        self._observers.clear()
        logger.info("Configuration manager shutdown")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(enable_hot_reload: bool = True) -> ConfigManager:
    """Get or create the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(enable_hot_reload=enable_hot_reload)
    return _config_manager


def get_current_config() -> PaperezConfig:
    """Get the current configuration."""
    return get_config_manager().get_config()