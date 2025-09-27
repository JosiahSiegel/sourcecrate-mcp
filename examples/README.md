# PaperezMCP Configuration Examples

Working config examples demonstrating source management and customization.

## 🚀 Quick Start

1. **Copy any example to `~/.paperez/config.yaml`**
2. **Restart PaperezMCP**
3. **Sources are immediately available!**

## 📁 Available Examples

### 1. `minimal_config_example.yaml`
**Minimal configuration** - Override specific sources
- ✅ **Demonstrates source override**: Disable CrossRef, customize Semantic Scholar
- ✅ **Built-in sources remain**: All other default sources still available
- ✅ **No API key needed**
- Perfect for: Simple customizations while keeping defaults

### 2. `open_access_config_example.yaml`
**Open access focused** - Custom category with selected sources
- ✅ **Custom category**: Open access sources only
- ✅ **Selected sources**: arXiv, PubMed Central, DOAJ, Europe PMC
- ✅ **No API key needed**
- Perfect for: Researchers prioritizing open access content

### 3. `simple_config_sources.yaml`
**User-only sources** - Disable defaults, use custom sources only
- ✅ **use_default_sources: false**: No built-in sources
- ✅ **Custom sources**: Europe PMC, DOAJ, custom API examples
- ✅ **Templates included**: CORE, custom REST API examples
- Perfect for: Complete control over available sources

### 4. `unified_config_system.yaml`
**Complete configuration** - All options demonstrated
- ✅ **All configuration options**: Sources, categories, routing, cache
- ✅ **Advanced features**: Query routing, custom categories, rate limiting
- ✅ **Documentation**: Inline comments explaining all options
- Perfect for: Power users, understanding all capabilities

## 🎯 Usage

```bash
# Copy entire config
cp examples/minimal_config_example.yaml ~/.paperez/config.yaml

# For user-only sources (disable all defaults)
cp examples/simple_config_sources.yaml ~/.paperez/config.yaml

# For complete configuration reference
cp examples/unified_config_system.yaml ~/.paperez/config.yaml
```

## 🔧 Configuration Options

### Built-in Source Control
```yaml
# Keep all built-in sources, allow overrides (default)
use_default_sources: true

# Disable all built-in sources, use only user sources
use_default_sources: false
```

### Source Override Behavior
- **Same name sources**: User config completely replaces built-in source
- **New sources**: Added alongside built-in sources
- **Environment override**: `PAPEREZ_USE_DEFAULT_SOURCES=false`

## ✅ Verification

All examples tested with latest configuration system:
- Source override functionality verified
- use_default_sources option tested
- Default source behavior confirmed

## 💡 Need Help?

See documentation for detailed guidance:
- `CONFIG_SOURCES_GUIDE.md`: Adding REST APIs as sources
- `CONFIGURATION.md`: Complete configuration reference
- Built-in config: `paperez_mcp/config/default_config.yaml`