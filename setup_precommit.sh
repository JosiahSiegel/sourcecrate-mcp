#!/bin/bash
# Setup script for MCP server pre-commit validation

echo "🔧 Setting up MCP server pre-commit validation..."

# Option 1: Use pre-commit framework (if available)
if command -v pre-commit &> /dev/null; then
    echo "📦 Found pre-commit, installing hooks..."
    pre-commit install
    echo "✅ Pre-commit hooks installed (manual git hook will be replaced)"
    echo "🧪 Testing hooks..."
    pre-commit run --all-files
else
    echo "⚠️ pre-commit not found, using Git hooks instead"

    # Option 2: Use Git hooks directly
    echo "📝 Installing Git pre-commit hook..."

    # Make sure scripts are executable
    chmod +x scripts/*.py

    # Install the Git hook (already created)
    if [ -f ".git/hooks/pre-commit" ]; then
        chmod +x .git/hooks/pre-commit
        echo "✅ Git pre-commit hook installed"
    else
        echo "❌ Git hook not found"
        exit 1
    fi

    # Test the validation
    echo "🧪 Testing MCP server validation..."
    python3 scripts/simple_mcp_check.py

    if [ $? -eq 0 ]; then
        echo "✅ MCP server validation working"
    else
        echo "❌ MCP server validation failed"
        exit 1
    fi
fi

echo ""
echo "🎉 Pre-commit validation setup complete!"
echo ""
echo "📋 What was installed:"
echo "  • MCP server syntax validation"
echo "  • Python file syntax checking"
echo "  • Ruff linting (matches CI workflow)"
echo "  • MyPy type checking (matches CI workflow)"
if command -v pre-commit &> /dev/null; then
    echo "  • Pre-commit framework hooks (replaced manual git hook)"
else
    echo "  • Manual git pre-commit hook"
fi
echo ""
echo "💡 Usage:"
echo "  • Hooks run automatically on 'git commit'"
echo "  • Manual test: python3 scripts/simple_mcp_check.py"
echo "  • Manual test all: python3 scripts/validate_mcp_server.py"
echo ""
echo "⚠️ Note: Commits will be rejected if MCP server has syntax errors"