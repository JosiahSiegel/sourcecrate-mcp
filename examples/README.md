# PaperezMCP Configuration Examples

Three working config examples for adding academic sources with just configuration files.

## 🚀 Quick Start

1. **Copy any example to `~/.paperez/config.yaml`**
2. **Restart PaperezMCP**
3. **New sources are immediately available!**

## 📁 Available Examples

### 1. `minimal_config_example.yaml`
**Just Europe PMC** - Simplest possible config
- ✅ **Europe PMC**: 39M+ life sciences papers
- ✅ **No API key needed**
- ✅ **Tested and working**
- Perfect for: Life sciences researchers, medical students

### 2. `open_access_config_example.yaml`
**Europe PMC + DOAJ** - Open access focused
- ✅ **Europe PMC**: 39M+ life sciences papers
- ✅ **DOAJ**: 2.1M+ peer-reviewed open access articles
- ✅ **No API key needed**
- ✅ **Tested and working**
- Perfect for: Researchers prioritizing open access content

### 3. `simple_config_sources.yaml`
**Full featured with templates** - Complete configuration guide
- ✅ **Europe PMC + DOAJ**: Working examples
- ✅ **CORE template**: For users with API keys
- ✅ **Custom source template**: Add any REST API
- ✅ **Documentation**: How to configure any source
- Perfect for: Power users, custom integrations

## 🎯 Usage

```bash
# Option 1: Copy entire config
cp examples/minimal_config_example.yaml ~/.paperez/config.yaml

# Option 2: Merge with existing config
# (copy the 'sources' and 'categories' sections)
```

## ✅ Verification

All examples tested with real API calls:
- Europe PMC: Returns papers for "covid vaccine", "climate change"
- DOAJ: Returns papers for "renewable energy", "artificial intelligence"

## 💡 Need Help?

See `CONFIG_SOURCES_GUIDE.md` for detailed instructions on:
- Adding any REST API as a source
- Field mapping configuration
- Authentication setup
- Troubleshooting tips